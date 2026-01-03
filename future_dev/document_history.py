"""Database logging and history retrieval for document analysis.

Tracks document analyses in SQLite for user history and audit trail.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path("document_analysis.sqlite")


class DocumentAnalysisDB:
    """Database interface for storing and retrieving document analysis history."""
    
    def __init__(self, db_path: str = "document_analysis.sqlite"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS document_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        username TEXT,
                        timestamp TEXT NOT NULL,
                        document_name TEXT,
                        original_question TEXT,
                        extracted_preview TEXT,
                        analysis_result TEXT,
                        persona TEXT,
                        document_type TEXT,
                        processing_time_ms REAL,
                        status TEXT,
                        error_message TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_user_id ON document_analysis(user_id)
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON document_analysis(timestamp)
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_user_timestamp ON document_analysis(user_id, timestamp)
                ''')
                conn.commit()
        except sqlite3.OperationalError as e:
            logger.warning(f"Could not initialize document_analysis table: {e}")
    
    def log_analysis(
        self,
        user_id: int,
        username: str,
        document_name: str,
        original_question: str,
        extracted_preview: str,
        analysis_result: str,
        persona: str,
        document_type: str,
        processing_time_ms: float,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> bool:
        """Log a document analysis to database.
        
        Args:
            user_id: Telegram user ID
            username: Telegram username
            document_name: Original document filename
            original_question: User's question/caption
            extracted_preview: First 500 chars of extracted text
            analysis_result: Kei/Kin response
            persona: 'kei' or 'kin'
            document_type: 'pdf', 'image', 'text', 'excel'
            processing_time_ms: Time taken to process
            status: 'success' or 'error'
            error_message: Error details if failed
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO document_analysis 
                    (user_id, username, timestamp, document_name, original_question, 
                     extracted_preview, analysis_result, persona, document_type, 
                     processing_time_ms, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    username,
                    datetime.now().isoformat(),
                    document_name,
                    original_question[:200],  # Truncate
                    extracted_preview[:500],  # Truncate
                    analysis_result[:2000],   # Truncate
                    persona,
                    document_type,
                    processing_time_ms,
                    status,
                    error_message[:200] if error_message else None
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to log analysis: {e}")
            return False
    
    def get_user_analysis_history(
        self,
        user_id: int,
        limit: int = 10,
        days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get analysis history for a user.
        
        Args:
            user_id: Telegram user ID
            limit: Maximum number of records to return
            days: Filter to last N days (None = all)
            
        Returns:
            List of analysis records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                where = "WHERE user_id = ?"
                params = [user_id]
                
                if days:
                    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
                    where += " AND timestamp > ?"
                    params.append(cutoff)
                
                rows = conn.execute(f'''
                    SELECT * FROM document_analysis
                    {where}
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', params + [limit]).fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to retrieve history: {e}")
            return []
    
    def get_analysis_by_id(self, analysis_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get specific analysis record.
        
        Args:
            analysis_id: Record ID
            user_id: Telegram user ID (for authorization)
            
        Returns:
            Analysis record or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                row = conn.execute('''
                    SELECT * FROM document_analysis
                    WHERE id = ? AND user_id = ?
                ''', (analysis_id, user_id)).fetchone()
                
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to retrieve analysis: {e}")
            return None
    
    def search_analyses(
        self,
        user_id: int,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search analyses by document name or question.
        
        Args:
            user_id: Telegram user ID
            query: Search term
            limit: Maximum results
            
        Returns:
            List of matching records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                search_term = f"%{query}%"
                rows = conn.execute('''
                    SELECT * FROM document_analysis
                    WHERE user_id = ? AND (
                        document_name LIKE ? OR 
                        original_question LIKE ? OR 
                        extracted_preview LIKE ?
                    )
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (user_id, search_term, search_term, search_term, limit)).fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to search analyses: {e}")
            return []
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics for user's analyses.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Statistics dictionary
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = conn.execute('''
                    SELECT
                        COUNT(*) as total_analyses,
                        COUNT(CASE WHEN status='success' THEN 1 END) as successful,
                        COUNT(CASE WHEN status='error' THEN 1 END) as failed,
                        COUNT(DISTINCT document_type) as document_types_used,
                        COUNT(CASE WHEN persona='kei' THEN 1 END) as kei_analyses,
                        COUNT(CASE WHEN persona='kin' THEN 1 END) as kin_analyses,
                        AVG(processing_time_ms) as avg_processing_time
                    FROM document_analysis
                    WHERE user_id = ?
                ''', (user_id,)).fetchone()
                
                if stats:
                    return {
                        'total_analyses': stats[0] or 0,
                        'successful': stats[1] or 0,
                        'failed': stats[2] or 0,
                        'document_types': stats[3] or 0,
                        'kei_analyses': stats[4] or 0,
                        'kin_analyses': stats[5] or 0,
                        'avg_processing_time_ms': round(stats[6], 2) if stats[6] else 0
                    }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
        
        return {
            'total_analyses': 0,
            'successful': 0,
            'failed': 0,
            'document_types': 0,
            'kei_analyses': 0,
            'kin_analyses': 0,
            'avg_processing_time_ms': 0
        }
    
    def delete_old_records(self, days: int = 90) -> int:
        """Delete analyses older than N days (cleanup).
        
        Args:
            days: Delete records older than this many days
            
        Returns:
            Number of records deleted
        """
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM document_analysis
                    WHERE timestamp < ?
                ''', (cutoff,))
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to delete old records: {e}")
            return 0


# Global instance
_db_instance = None

def get_analysis_db() -> DocumentAnalysisDB:
    """Get or create global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DocumentAnalysisDB()
    return _db_instance
