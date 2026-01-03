"""Activity monitoring and statistics for PerisAI bot.

Tracks bot usage, query statistics, error rates, and user activity.
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class ActivityMonitor:
    """Monitor and report on bot activity and performance metrics."""
    
    def __init__(self, db_path: str = "usage_metrics.sqlite"):
        """Initialize activity monitor with metrics database.
        
        Args:
            db_path: Path to SQLite metrics database
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Ensure metrics table exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ts TEXT NOT NULL,
                        persona TEXT,
                        query_type TEXT,
                        success INTEGER,
                        latency_ms REAL,
                        user_hash TEXT,
                        username TEXT,
                        error TEXT,
                        raw_query TEXT
                    )
                ''')
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_persona ON events(persona);")
                conn.commit()
        except sqlite3.OperationalError as e:
            logger.warning(f"Could not initialize events table: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """Get health metrics for last 24h and 7d.
        
        Returns:
            Dict with health status (success rate, avg latency, unique users)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                now = datetime.now()
                
                # Last 24h
                cutoff_24h = (now - timedelta(hours=24)).isoformat()
                row_24h = conn.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
                        AVG(latency_ms) as avg_latency,
                        COUNT(DISTINCT user_hash) as unique_users
                    FROM events
                    WHERE ts > ?
                ''', (cutoff_24h,)).fetchone()
                
                # Last 7d
                cutoff_7d = (now - timedelta(days=7)).isoformat()
                row_7d = conn.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
                        AVG(latency_ms) as avg_latency,
                        COUNT(DISTINCT user_hash) as unique_users
                    FROM events
                    WHERE ts > ?
                ''', (cutoff_7d,)).fetchone()
                
                def _format_metrics(row):
                    if not row or row[0] == 0:
                        return {
                            'total_queries': 0,
                            'success_rate': 100,
                            'avg_latency_ms': 0,
                            'unique_users': 0
                        }
                    total, successful, avg_latency, unique_users = row
                    success_rate = (successful / total * 100) if total > 0 else 0
                    avg_latency_ms = int(avg_latency * 1000) if avg_latency else 0
                    return {
                        'total_queries': total,
                        'success_rate': success_rate,
                        'avg_latency_ms': avg_latency_ms,
                        'unique_users': unique_users or 0
                    }
                
                return {
                    'last_24h': _format_metrics(row_24h),
                    'last_7d': _format_metrics(row_7d)
                }
        except Exception as e:
            logger.error(f"Error getting health check: {e}")
            return {
                'last_24h': {'total_queries': 0, 'success_rate': 0, 'avg_latency_ms': 0, 'unique_users': 0},
                'last_7d': {'total_queries': 0, 'success_rate': 0, 'avg_latency_ms': 0, 'unique_users': 0}
            }
    
    def query_stats(self, hours: int = 24, limit: int = 10) -> Dict[str, Dict[str, Any]]:
        """Get query statistics by type for the last N hours.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of query types to return
            
        Returns:
            Dict mapping query_type -> {count, success_rate}
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                rows = conn.execute('''
                    SELECT 
                        query_type,
                        COUNT(*) as count,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
                    FROM events
                    WHERE ts > ?
                    GROUP BY query_type
                    ORDER BY count DESC
                    LIMIT ?
                ''', (cutoff, limit)).fetchall()
                
                stats = {}
                for query_type, count, successful in rows:
                    success_rate = (successful / count * 100) if count > 0 else 0
                    stats[query_type or 'unknown'] = {
                        'count': count,
                        'success_rate': success_rate
                    }
                
                return stats
        except Exception as e:
            logger.error(f"Error getting query stats: {e}")
            return {}
    
    def persona_usage(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics by persona.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dict mapping persona -> {count, success_rate}
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                rows = conn.execute('''
                    SELECT 
                        persona,
                        COUNT(*) as count,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
                    FROM events
                    WHERE ts > ? AND persona IS NOT NULL
                    GROUP BY persona
                    ORDER BY count DESC
                ''', (cutoff,)).fetchall()
                
                stats = {}
                for persona, count, successful in rows:
                    success_rate = (successful / count * 100) if count > 0 else 0
                    stats[persona or 'unknown'] = {
                        'count': count,
                        'success_rate': success_rate
                    }
                
                return stats
        except Exception as e:
            logger.error(f"Error getting persona usage: {e}")
            return {}
    
    def top_users(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by query count for the last N hours.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of users to return
            
        Returns:
            List of dicts with user_hash, username, query_count, success_rate
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                rows = conn.execute('''
                    SELECT 
                        user_hash,
                        username,
                        COUNT(*) as count,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
                    FROM events
                    WHERE ts > ? AND user_hash IS NOT NULL AND user_hash != 'anon'
                    GROUP BY user_hash
                    ORDER BY count DESC
                    LIMIT ?
                ''', (cutoff, limit)).fetchall()
                
                users = []
                for user_hash, username, count, successful in rows:
                    success_rate = (successful / count * 100) if count > 0 else 0
                    users.append({
                        'user_hash': user_hash,
                        'username': username or f'user_{user_hash}',
                        'query_count': count,
                        'success_rate': success_rate
                    })
                
                return users
        except Exception as e:
            logger.error(f"Error getting top users: {e}")
            return []
    
    def error_summary(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """Get summary of recent errors for the last N hours.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of error types to return
            
        Returns:
            List of dicts with error description, count
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                rows = conn.execute('''
                    SELECT 
                        error,
                        COUNT(*) as count
                    FROM events
                    WHERE ts > ? AND success = 0 AND error IS NOT NULL AND error != ''
                    GROUP BY error
                    ORDER BY count DESC
                    LIMIT ?
                ''', (cutoff, limit)).fetchall()
                
                errors = []
                for error, count in rows:
                    errors.append({
                        'error': error or 'Unknown error',
                        'count': count
                    })
                
                return errors
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return []
    
    def hourly_timeline(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get hourly query timeline for the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of dicts with hour, query_count, success_count
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                rows = conn.execute('''
                    SELECT 
                        substr(ts, 1, 13) as hour,
                        COUNT(*) as total,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
                    FROM events
                    WHERE ts > ?
                    GROUP BY hour
                    ORDER BY hour DESC
                ''', (cutoff,)).fetchall()
                
                timeline = []
                for hour, total, successful in rows:
                    timeline.append({
                        'hour': hour,
                        'query_count': total,
                        'success_count': successful or 0
                    })
                
                return timeline
        except Exception as e:
            logger.error(f"Error getting hourly timeline: {e}")
            return []


if __name__ == '__main__':
    # Example usage
    monitor = ActivityMonitor()
    print("Health Check:")
    print(monitor.health_check())
    print("\nQuery Stats (last 24h):")
    print(monitor.query_stats())
    print("\nTop Users (last 24h):")
    print(monitor.top_users())
    print("\nRecent Errors:")
    print(monitor.error_summary())
