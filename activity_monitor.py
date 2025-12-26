#!/usr/bin/env python3
"""Real-time user activity monitoring dashboard for PerisAI Bot.

Provides insights into:
- Active users and their query patterns
- Query success rates and response times
- Most common query types
- Error tracking and diagnostics
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict, Counter


class ActivityMonitor:
    """Monitor user activity from usage_metrics.sqlite."""
    
    def __init__(self, db_path: str = "usage_metrics.sqlite"):
        self.db_path = Path(db_path)
        
    def get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def user_count(self, hours: int = 24) -> int:
        """Count unique users in last N hours."""
        conn = self.get_conn()
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        count = conn.execute(
            "SELECT COUNT(DISTINCT user_hash) FROM events WHERE ts > ?",
            (cutoff,)
        ).fetchone()[0]
        conn.close()
        return count
    
    def query_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get query statistics for last N hours."""
        conn = self.get_conn()
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        rows = conn.execute("""
            SELECT 
                query_type,
                COUNT(*) as count,
                SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successes,
                AVG(latency_ms) as avg_latency
            FROM events
            WHERE ts > ?
            GROUP BY query_type
            ORDER BY count DESC
        """, (cutoff,)).fetchall()
        
        stats = {}
        for row in rows:
            stats[row['query_type']] = {
                'count': row['count'],
                'successes': row['successes'],
                'failures': row['count'] - (row['successes'] or 0),
                'success_rate': (row['successes'] / row['count'] * 100) if row['count'] > 0 else 0,
                'avg_latency_ms': round(row['avg_latency'] or 0, 1)
            }
        
        conn.close()
        return stats
    
    def error_summary(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common errors in last N hours."""
        conn = self.get_conn()
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        rows = conn.execute("""
            SELECT 
                error,
                COUNT(*) as count,
                query_type,
                persona
            FROM events
            WHERE ts > ? AND success=0 AND error IS NOT NULL AND error != ''
            GROUP BY error
            ORDER BY count DESC
            LIMIT ?
        """, (cutoff, limit)).fetchall()
        
        errors = [dict(row) for row in rows]
        conn.close()
        return errors
    
    def top_users(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most active users in last N hours."""
        conn = self.get_conn()
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        rows = conn.execute("""
            SELECT 
                user_hash,
                username,
                COUNT(*) as query_count,
                SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successes,
                AVG(latency_ms) as avg_latency
            FROM events
            WHERE ts > ?
            GROUP BY user_hash
            ORDER BY query_count DESC
            LIMIT ?
        """, (cutoff, limit)).fetchall()
        
        users = []
        for row in rows:
            users.append({
                'user_hash': row['user_hash'],
                'username': row['username'] or 'unknown',
                'query_count': row['query_count'],
                'successes': row['successes'],
                'failures': row['query_count'] - (row['successes'] or 0),
                'success_rate': (row['successes'] / row['query_count'] * 100) if row['query_count'] > 0 else 0,
                'avg_latency_ms': round(row['avg_latency'] or 0, 1)
            })
        
        conn.close()
        return users
    
    def persona_usage(self, hours: int = 24) -> Dict[str, Any]:
        """Get persona (Kei/Kin) usage breakdown."""
        conn = self.get_conn()
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        rows = conn.execute("""
            SELECT 
                persona,
                COUNT(*) as count,
                SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successes,
                AVG(latency_ms) as avg_latency
            FROM events
            WHERE ts > ?
            GROUP BY persona
            ORDER BY count DESC
        """, (cutoff,)).fetchall()
        
        stats = {}
        for row in rows:
            stats[row['persona']] = {
                'count': row['count'],
                'successes': row['successes'],
                'failures': row['count'] - (row['successes'] or 0),
                'success_rate': (row['successes'] / row['count'] * 100) if row['count'] > 0 else 0,
                'avg_latency_ms': round(row['avg_latency'] or 0, 1)
            }
        
        conn.close()
        return stats
    
    def timeline(self, hours: int = 24, interval_minutes: int = 60) -> List[Dict[str, Any]]:
        """Get activity timeline by interval."""
        conn = self.get_conn()
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        rows = conn.execute(f"""
            SELECT 
                strftime('%Y-%m-%d %H:00:00', ts) as hour,
                COUNT(*) as count,
                SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successes
            FROM events
            WHERE ts > ?
            GROUP BY hour
            ORDER BY hour
        """, (cutoff,)).fetchall()
        
        timeline = []
        for row in rows:
            timeline.append({
                'time': row['hour'],
                'queries': row['count'],
                'successes': row['successes'],
                'failures': row['count'] - (row['successes'] or 0),
                'success_rate': (row['successes'] / row['count'] * 100) if row['count'] > 0 else 0
            })
        
        conn.close()
        return timeline
    
    def health_check(self) -> Dict[str, Any]:
        """Overall bot health summary."""
        conn = self.get_conn()
        cutoff_24h = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        cutoff_7d = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        total_queries = conn.execute(
            "SELECT COUNT(*) FROM events WHERE ts > ?", (cutoff_24h,)
        ).fetchone()[0]
        
        successful = conn.execute(
            "SELECT COUNT(*) FROM events WHERE ts > ? AND success=1", (cutoff_24h,)
        ).fetchone()[0]
        
        unique_users_24h = conn.execute(
            "SELECT COUNT(DISTINCT user_hash) FROM events WHERE ts > ?", (cutoff_24h,)
        ).fetchone()[0]
        
        unique_users_7d = conn.execute(
            "SELECT COUNT(DISTINCT user_hash) FROM events WHERE ts > ?", (cutoff_7d,)
        ).fetchone()[0]
        
        avg_latency = conn.execute(
            "SELECT AVG(latency_ms) FROM events WHERE ts > ? AND success=1", (cutoff_24h,)
        ).fetchone()[0]
        
        conn.close()
        
        return {
            'last_24h': {
                'total_queries': total_queries,
                'successful': successful,
                'failed': total_queries - successful,
                'success_rate': (successful / total_queries * 100) if total_queries > 0 else 0,
                'avg_latency_ms': round(avg_latency or 0, 1),
                'unique_users': unique_users_24h
            },
            'last_7d': {
                'unique_users': unique_users_7d
            }
        }


def format_table(data: List[Dict], headers: List[str]) -> str:
    """Format list of dicts as text table."""
    if not data:
        return "No data"
    
    # Calculate column widths
    widths = {h: len(h) for h in headers}
    for row in data:
        for h in headers:
            val = str(row.get(h, ''))
            widths[h] = max(widths[h], len(val))
    
    # Format rows
    lines = []
    header_row = " | ".join(f"{h:<{widths[h]}}" for h in headers)
    lines.append(header_row)
    lines.append("-" * len(header_row))
    
    for row in data:
        row_str = " | ".join(f"{str(row.get(h, '')):<{widths[h]}}" for h in headers)
        lines.append(row_str)
    
    return "\n".join(lines)


def print_dashboard(monitor: ActivityMonitor):
    """Print formatted activity dashboard."""
    print("\n" + "=" * 80)
    print("📊 PerisAI Bot Activity Monitor".center(80))
    print("=" * 80)
    
    # Health summary
    health = monitor.health_check()
    print("\n🏥 Bot Health (Last 24 Hours)")
    print(f"  Total Queries    : {health['last_24h']['total_queries']}")
    print(f"  Successful       : {health['last_24h']['successful']} ({health['last_24h']['success_rate']:.1f}%)")
    print(f"  Failed           : {health['last_24h']['failed']}")
    print(f"  Avg Response     : {health['last_24h']['avg_latency_ms']} ms")
    print(f"  Unique Users     : {health['last_24h']['unique_users']}")
    print(f"  Weekly Users     : {health['last_7d']['unique_users']}")
    
    # Query statistics
    print("\n📈 Query Types")
    query_stats = monitor.query_stats(hours=24)
    if query_stats:
        rows = [
            {
                'Type': qtype,
                'Count': stats['count'],
                'Success %': f"{stats['success_rate']:.0f}%",
                'Avg Latency': f"{stats['avg_latency_ms']}ms"
            }
            for qtype, stats in query_stats.items()
        ]
        print(format_table(rows, ['Type', 'Count', 'Success %', 'Avg Latency']))
    
    # Persona usage
    print("\n🎭 Persona Usage")
    persona_stats = monitor.persona_usage(hours=24)
    if persona_stats:
        rows = [
            {
                'Persona': name,
                'Queries': stats['count'],
                'Success %': f"{stats['success_rate']:.0f}%",
                'Latency': f"{stats['avg_latency_ms']}ms"
            }
            for name, stats in persona_stats.items()
        ]
        print(format_table(rows, ['Persona', 'Queries', 'Success %', 'Latency']))
    
    # Top users
    print("\n👥 Most Active Users")
    top_users = monitor.top_users(hours=24, limit=5)
    if top_users:
        rows = [
            {
                'User': u['username'],
                'Queries': u['query_count'],
                'Success %': f"{u['success_rate']:.0f}%",
                'Latency': f"{u['avg_latency_ms']}ms"
            }
            for u in top_users
        ]
        print(format_table(rows, ['User', 'Queries', 'Success %', 'Latency']))
    
    # Recent errors
    print("\n⚠️ Recent Errors")
    errors = monitor.error_summary(hours=24, limit=5)
    if errors:
        rows = [
            {
                'Error': e['error'][:50] if e['error'] else 'Unknown',
                'Count': e['count'],
                'Type': e['query_type']
            }
            for e in errors
        ]
        print(format_table(rows, ['Error', 'Count', 'Type']))
    else:
        print("  ✅ No errors in last 24 hours!")
    
    # Activity timeline
    print("\n📅 Activity Timeline (Last 24 Hours)")
    timeline = monitor.timeline(hours=24)
    if timeline:
        for entry in timeline[-8:]:  # Last 8 hours
            bar_length = entry['queries'] // 2
            bar = "█" * bar_length
            print(f"  {entry['time']} {bar} ({entry['queries']} queries, {entry['success_rate']:.0f}% success)")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    monitor = ActivityMonitor()
    print_dashboard(monitor)
