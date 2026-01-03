#!/usr/bin/env python3
"""
Example: Using PDF Dataset with Kei Analysis

Shows how to:
1. Ingest PDFs from a folder
2. Use them for Kei's contextual analysis
3. List and manage the knowledge base
"""

import sys
from pathlib import Path

# Example 1: Ingest a folder of PDFs
def example_ingest_folder():
    """Ingest all PDFs from a specific folder."""
    from pdf_dataset_ingestion import PDFDatasetBuilder
    
    print("="*60)
    print("EXAMPLE 1: Ingest PDF Folder")
    print("="*60)
    
    builder = PDFDatasetBuilder(kb_dir="knowledge_base")
    
    # Replace with your actual folder path
    folder_path = "./sample_pdfs"
    
    print(f"Ingesting PDFs from: {folder_path}")
    result = builder.ingest_folder(
        folder_path=folder_path,
        category="market_research",
        max_pages_per_file=100,
        exclude_small_files=True
    )
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"\n✅ Success!")
        print(f"   Processed: {result['statistics']['processed']} files")
        print(f"   Total pages: {result['statistics']['total_pages']}")
        print(f"   Total characters: {result['statistics']['total_chars']:,}")


# Example 2: List all ingested documents
def example_list_documents():
    """List all documents in the knowledge base."""
    from pdf_dataset_ingestion import PDFDatasetBuilder
    
    print("\n" + "="*60)
    print("EXAMPLE 2: List Ingested Documents")
    print("="*60)
    
    builder = PDFDatasetBuilder(kb_dir="knowledge_base")
    docs = builder.list_ingested_documents()
    
    if not docs:
        print("📭 No documents in knowledge base yet")
        print("   Run Example 1 first to ingest PDFs")
    else:
        print("📚 Knowledge Base Contents:\n")
        for category, files in docs.items():
            print(f"📂 {category.upper()}")
            for file_info in files:
                print(f"   • {file_info['filename']}")
                print(f"     Size: {file_info['size_kb']:.1f} KB")
                print(f"     Chars: {file_info['chars']:,}\n")


# Example 3: Get context for a query
def example_get_context():
    """Retrieve PDF context for a specific query."""
    from pdf_dataset_ingestion import KeiPDFAnalyzer
    
    print("\n" + "="*60)
    print("EXAMPLE 3: Retrieve Context for Query")
    print("="*60)
    
    analyzer = KeiPDFAnalyzer(kb_dir="knowledge_base")
    
    # Example query
    query = "What are the upcoming auction trends?"
    
    print(f"Query: {query}")
    print("\nRetrieving relevant context from PDFs...\n")
    
    context = analyzer.get_pdf_context(query, top_k=2)
    
    if not context:
        print("❌ No relevant context found")
        print("   (Make sure you've ingested PDFs first)")
    else:
        print(context[:500] + "..." if len(context) > 500 else context)


# Example 4: Enhance a prompt with PDF context
def example_enhance_prompt():
    """Show how to enhance Kei's system prompt with PDF context."""
    from pdf_dataset_ingestion import KeiPDFAnalyzer
    
    print("\n" + "="*60)
    print("EXAMPLE 4: Enhanced Prompt with PDF Context")
    print("="*60)
    
    analyzer = KeiPDFAnalyzer(kb_dir="knowledge_base")
    
    # Original system prompt (simplified)
    original_prompt = """You are Kei, a bond market expert. 
Answer questions about Indonesian bond markets, auctions, and yields.
Use professional language and provide specific examples."""
    
    # User's query
    query = "Analyze bond auction demand trends"
    
    print(f"User Query: {query}\n")
    
    # Enhance the prompt
    enhanced_prompt = analyzer.enhance_prompt(query, original_prompt)
    
    print("Original prompt length:", len(original_prompt), "chars")
    print("Enhanced prompt length:", len(enhanced_prompt), "chars")
    print("\nEnhanced prompt includes PDF context injected automatically!")
    
    if enhanced_prompt != original_prompt:
        print("✅ PDF context successfully added")
    else:
        print("❌ No PDF context available (ingest PDFs first)")


# Example 5: Knowledge base summary
def example_kb_summary():
    """Show knowledge base statistics."""
    from pdf_dataset_ingestion import KeiPDFAnalyzer
    
    print("\n" + "="*60)
    print("EXAMPLE 5: Knowledge Base Summary")
    print("="*60)
    
    analyzer = KeiPDFAnalyzer(kb_dir="knowledge_base")
    summary = analyzer.get_knowledge_summary()
    
    print(f"📊 Total Documents: {summary['total_documents']}")
    
    if summary['total_documents'] == 0:
        print("   (No documents ingested yet)")
    else:
        print("\nDocuments by Category:")
        for category, files in summary['categories'].items():
            print(f"  📂 {category}: {len(files)} files")
        
        print("\nDetailed List:")
        for doc in summary['documents'][:5]:  # Show first 5
            print(f"  • {doc['filename']}")
            print(f"    Size: {doc['size_kb']:.1f} KB")
        
        if len(summary['documents']) > 5:
            print(f"  ... and {len(summary['documents']) - 5} more")


# Example 6: Single PDF ingestion
def example_single_pdf():
    """Ingest a single PDF file."""
    from pdf_dataset_ingestion import PDFDatasetBuilder
    
    print("\n" + "="*60)
    print("EXAMPLE 6: Ingest Single PDF")
    print("="*60)
    
    builder = PDFDatasetBuilder(kb_dir="knowledge_base")
    
    # Replace with actual PDF path
    pdf_path = "./sample_pdfs/example.pdf"
    
    print(f"Ingesting: {pdf_path}")
    result = builder.ingest_single_pdf(pdf_path, category="reports")
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Success!")
        print(f"   Saved as: {result['saved_as']}")
        print(f"   Category: {result['category']}")
        print(f"   Pages: {result['pages']}")
        print(f"   Characters: {result['chars']:,}")


# Example 7: Integration with Kei's analysis
def example_kei_integration():
    """Show how to use PDFs in Kei's analysis (simulated)."""
    from pdf_dataset_ingestion import KeiPDFAnalyzer
    
    print("\n" + "="*60)
    print("EXAMPLE 7: Kei Analysis with PDF Context")
    print("="*60)
    
    analyzer = KeiPDFAnalyzer(kb_dir="knowledge_base")
    
    # Simulated user query
    user_query = "Compare current auction demand with historical trends"
    
    print(f"User: {user_query}")
    print("\nKei is analyzing with PDF context...\n")
    
    # Get context
    context = analyzer.get_pdf_context(user_query, top_k=2)
    
    if context:
        print("✅ Kei will use PDF context:")
        print(context[:300] + "..." if len(context) > 300 else context)
        print("\n[Kei's response would include insights from PDFs...]")
    else:
        print("❌ No PDF context available")


# Main menu
def main():
    """Run examples."""
    print("\n" + "="*60)
    print("PDF DATASET FOR KEI ANALYSIS - EXAMPLES")
    print("="*60)
    print("\nThis script demonstrates:")
    print("1. Ingest PDFs from a folder")
    print("2. List ingested documents")
    print("3. Retrieve context for queries")
    print("4. Enhance prompts with PDF context")
    print("5. View knowledge base summary")
    print("6. Ingest single PDF files")
    print("7. Integrate PDFs with Kei's analysis")
    
    print("\n" + "-"*60)
    print("Running all examples...\n")
    
    # Run examples (wrap in try/except to continue on errors)
    try:
        example_list_documents()
    except Exception as e:
        print(f"⚠️  Example 2 skipped: {e}")
    
    try:
        example_kb_summary()
    except Exception as e:
        print(f"⚠️  Example 5 skipped: {e}")
    
    try:
        example_get_context()
    except Exception as e:
        print(f"⚠️  Example 3 skipped: {e}")
    
    try:
        example_enhance_prompt()
    except Exception as e:
        print(f"⚠️  Example 4 skipped: {e}")
    
    try:
        example_kei_integration()
    except Exception as e:
        print(f"⚠️  Example 7 skipped: {e}")
    
    # These examples need actual files, so they're commented
    print("\n" + "-"*60)
    print("📝 To run the full examples with PDF ingestion:")
    print("\n1. Create a folder with PDF files:")
    print("   mkdir -p sample_pdfs")
    print("   cp /path/to/your/pdfs/*.pdf sample_pdfs/")
    print("\n2. Then uncomment these in the main() function:")
    print("   - example_ingest_folder()")
    print("   - example_single_pdf()")
    print("\n3. Run this script:")
    print("   python pdf_dataset_examples.py")
    
    print("\n" + "-"*60)
    print("✅ Examples completed!")
    print("\nFor more details, see PDF_DATASET_INTEGRATION.md")


if __name__ == "__main__":
    main()
