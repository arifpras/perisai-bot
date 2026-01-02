"""
PDF Dataset Ingestion Module for Kei Analysis

Converts multiple PDFs from a folder into a searchable knowledge base
that Kei can use for analysis and contextual reasoning.

Usage:
    python pdf_dataset_ingestion.py --folder /path/to/pdfs
    Or programmatically:
    from pdf_dataset_ingestion import PDFDatasetBuilder
    builder = PDFDatasetBuilder()
    builder.ingest_folder('/path/to/pdfs', category='reports')
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import PyPDF2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFDatasetBuilder:
    """Builds a searchable knowledge base from PDF files."""
    
    def __init__(self, kb_dir: str = "knowledge_base", enable_caching: bool = True):
        """
        Initialize the PDF dataset builder.
        
        Args:
            kb_dir: Directory where knowledge base will be stored
            enable_caching: Cache extracted text to avoid re-processing
        """
        self.kb_dir = Path(kb_dir)
        self.kb_dir.mkdir(exist_ok=True)
        self.enable_caching = enable_caching
        self.cache_file = self.kb_dir / ".pdf_cache.json"
        self.cache = self._load_cache() if enable_caching else {}
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'skipped': 0,
            'failed': 0,
            'total_pages': 0,
            'total_chars': 0
        }
    
    def _load_cache(self) -> Dict:
        """Load cache of already processed PDFs."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save cache of processed PDFs."""
        if self.enable_caching:
            try:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.cache, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to save cache: {e}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of file for cache validation."""
        try:
            stat = file_path.stat()
            return f"{stat.st_size}_{stat.st_mtime}"
        except Exception:
            return None
    
    def extract_text_from_pdf(self, pdf_path: Path, max_pages: Optional[int] = None) -> str:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to extract (None = all)
        
        Returns:
            Extracted text content
        """
        text = []
        page_count = 0
        
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                num_pages = len(reader.pages)
                
                # Extract up to max_pages
                pages_to_extract = min(num_pages, max_pages) if max_pages else num_pages
                
                for i in range(pages_to_extract):
                    try:
                        page = reader.pages[i]
                        page_text = page.extract_text()
                        if page_text:
                            text.append(f"[Page {i+1}]\n{page_text}\n")
                            page_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to extract page {i+1} from {pdf_path.name}: {e}")
                        continue
                
                self.stats['total_pages'] += page_count
        except Exception as e:
            logger.error(f"Failed to read PDF {pdf_path.name}: {e}")
            self.stats['failed'] += 1
            return None
        
        return "".join(text) if text else None
    
    def ingest_folder(
        self,
        folder_path: str,
        category: str = "documents",
        max_pages_per_file: Optional[int] = None,
        exclude_small_files: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest all PDFs from a folder into the knowledge base.
        
        Args:
            folder_path: Path to folder containing PDFs
            category: Category for organizing documents
            max_pages_per_file: Limit pages extracted per PDF (None = no limit)
            exclude_small_files: Skip PDFs smaller than 1KB
        
        Returns:
            Ingestion summary with statistics
        """
        folder = Path(folder_path)
        if not folder.exists():
            logger.error(f"Folder not found: {folder_path}")
            return {'error': f"Folder not found: {folder_path}"}
        
        if not folder.is_dir():
            logger.error(f"Not a directory: {folder_path}")
            return {'error': f"Not a directory: {folder_path}"}
        
        # Find all PDF files
        pdf_files = list(folder.glob("**/*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {folder_path}")
            return {'warning': "No PDF files found"}
        
        self.stats['total_files'] = len(pdf_files)
        logger.info(f"Found {len(pdf_files)} PDF files in {folder_path}")
        
        # Create category directory in knowledge base
        category_dir = self.kb_dir / category
        category_dir.mkdir(exist_ok=True)
        
        processed_files = []
        
        for pdf_file in pdf_files:
            try:
                # Check file size
                file_size = pdf_file.stat().st_size
                if exclude_small_files and file_size < 1024:
                    logger.info(f"Skipping tiny file: {pdf_file.name} ({file_size} bytes)")
                    self.stats['skipped'] += 1
                    continue
                
                # Check cache
                file_hash = self._get_file_hash(pdf_file)
                cache_key = str(pdf_file)
                
                if cache_key in self.cache and self.cache[cache_key]['hash'] == file_hash:
                    logger.info(f"Using cached version: {pdf_file.name}")
                    text = self.cache[cache_key]['text']
                    self.stats['skipped'] += 1
                else:
                    # Extract text
                    logger.info(f"Processing: {pdf_file.name} ({file_size / 1024:.1f} KB)")
                    text = self.extract_text_from_pdf(pdf_file, max_pages=max_pages_per_file)
                    
                    if not text:
                        logger.warning(f"No text extracted from {pdf_file.name}")
                        self.stats['failed'] += 1
                        continue
                    
                    # Update cache
                    self.cache[cache_key] = {
                        'hash': file_hash,
                        'text': text,
                        'cached_at': datetime.now().isoformat(),
                        'file_size': file_size
                    }
                
                # Save to knowledge base
                output_filename = f"{pdf_file.stem}.txt"
                output_path = category_dir / output_filename
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                self.stats['total_chars'] += len(text)
                self.stats['processed'] += 1
                processed_files.append({
                    'filename': pdf_file.name,
                    'saved_as': output_filename,
                    'category': category,
                    'size_kb': file_size / 1024,
                    'chars': len(text)
                })
                
                logger.info(f"✅ Saved: {output_filename} ({len(text)} chars)")
            
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")
                self.stats['failed'] += 1
        
        # Save cache
        self._save_cache()
        
        # Return summary
        summary = {
            'status': 'success',
            'folder': str(folder),
            'category': category,
            'statistics': self.stats,
            'processed_files': processed_files,
            'knowledge_base_dir': str(self.kb_dir / category)
        }
        
        logger.info(f"\n{'='*60}")
        logger.info("INGESTION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total files: {self.stats['total_files']}")
        logger.info(f"Processed: {self.stats['processed']}")
        logger.info(f"Skipped (cached): {self.stats['skipped']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Total pages: {self.stats['total_pages']}")
        logger.info(f"Total chars: {self.stats['total_chars']:,}")
        logger.info(f"Knowledge base: {self.kb_dir / category}")
        
        return summary
    
    def ingest_single_pdf(self, pdf_path: str, category: str = "documents") -> Dict[str, Any]:
        """
        Ingest a single PDF file.
        
        Args:
            pdf_path: Path to PDF file
            category: Category for organizing document
        
        Returns:
            Ingestion result
        """
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            return {'error': f"File not found: {pdf_path}"}
        
        if not pdf_file.suffix.lower() == '.pdf':
            return {'error': f"Not a PDF file: {pdf_path}"}
        
        # Extract text
        logger.info(f"Processing: {pdf_file.name}")
        text = self.extract_text_from_pdf(pdf_file)
        
        if not text:
            return {'error': f"No text could be extracted from {pdf_file.name}"}
        
        # Save to knowledge base
        category_dir = self.kb_dir / category
        category_dir.mkdir(exist_ok=True)
        
        output_filename = f"{pdf_file.stem}.txt"
        output_path = category_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"✅ Saved: {output_filename}")
        
        return {
            'status': 'success',
            'file': pdf_file.name,
            'saved_as': output_filename,
            'category': category,
            'chars': len(text),
            'pages': text.count('[Page ')
        }
    
    def list_ingested_documents(self) -> Dict[str, Any]:
        """List all ingested documents by category."""
        documents = {}
        
        for category_dir in self.kb_dir.iterdir():
            if category_dir.is_dir() and category_dir.name != '__pycache__' and not category_dir.name.startswith('.'):
                files = list(category_dir.glob("*.txt"))
                if files:
                    documents[category_dir.name] = [
                        {
                            'filename': f.name,
                            'size_kb': f.stat().st_size / 1024,
                            'chars': len(f.read_text(encoding='utf-8'))
                        }
                        for f in files
                    ]
        
        return documents
    
    def clear_category(self, category: str) -> bool:
        """Delete all documents in a category."""
        category_dir = self.kb_dir / category
        if category_dir.exists():
            import shutil
            try:
                shutil.rmtree(category_dir)
                logger.info(f"Cleared category: {category}")
                return True
            except Exception as e:
                logger.error(f"Failed to clear category {category}: {e}")
                return False
        return False


class KeiPDFAnalyzer:
    """Integration layer for PDF dataset with Kei's analysis."""
    
    def __init__(self, kb_dir: str = "knowledge_base"):
        """Initialize Kei's PDF analyzer."""
        from rag_system import RAGIntegration
        self.rag = RAGIntegration(kb_dir=kb_dir)
    
    def get_pdf_context(self, query: str, top_k: int = 3) -> str:
        """
        Get context from PDF dataset for Kei's analysis.
        
        Args:
            query: User's question
            top_k: Number of document excerpts to include
        
        Returns:
            Formatted context for prompt injection
        """
        return self.rag.kb.get_context(query, top_k=top_k)
    
    def enhance_prompt(self, query: str, system_prompt: str) -> str:
        """
        Enhance Kei's system prompt with PDF dataset context.
        
        Args:
            query: User's question
            system_prompt: Original system prompt
        
        Returns:
            Enhanced prompt with PDF context
        """
        return self.rag.enhance_kei_prompt(query, system_prompt)
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get summary of PDF knowledge base."""
        return self.rag.get_kb_summary()


# ============================================================================
# COMMAND-LINE INTERFACE
# ============================================================================

def main():
    """Command-line interface for PDF ingestion."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ingest PDF files into knowledge base for Kei analysis"
    )
    parser.add_argument(
        "--folder",
        type=str,
        required=True,
        help="Path to folder containing PDF files"
    )
    parser.add_argument(
        "--category",
        type=str,
        default="documents",
        help="Category name for organizing documents (default: documents)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum pages to extract per PDF (default: all)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all ingested documents"
    )
    parser.add_argument(
        "--kb-dir",
        type=str,
        default="knowledge_base",
        help="Knowledge base directory (default: knowledge_base)"
    )
    
    args = parser.parse_args()
    
    builder = PDFDatasetBuilder(kb_dir=args.kb_dir)
    
    if args.list:
        # List all documents
        docs = builder.list_ingested_documents()
        print("\n" + "="*60)
        print("INGESTED DOCUMENTS")
        print("="*60)
        for category, files in docs.items():
            print(f"\n📂 {category}")
            for file_info in files:
                print(f"   📄 {file_info['filename']} ({file_info['size_kb']:.1f} KB)")
    else:
        # Ingest folder
        result = builder.ingest_folder(
            args.folder,
            category=args.category,
            max_pages_per_file=args.max_pages
        )
        
        # Print result
        print("\n" + "="*60)
        print("INGESTION RESULT")
        print("="*60)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
