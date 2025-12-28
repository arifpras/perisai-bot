#!/usr/bin/env python3
"""Common monitoring tasks and utilities for PerisAI Bot activity analysis."""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from activity_monitor import ActivityMonitor


def export_activity_report(hours: int = 24, output_file: Optional[str] = None) -> dict:
    """Export activity metrics to JSON file.
    
    Args:
        hours: Time window to analyze (default 24)
        output_file: Output file path (default: activity_report_{timestamp}.json)
    
    Returns:
        Dictionary with report data
    """
    monitor = ActivityMonitor()
    
    report = {
        'generated': datetime.utcnow().isoformat(),
        'window_hours': hours,
        'health': monitor.health_check(),
        'query_stats': monitor.query_stats(hours=hours),
        'persona_usage': monitor.persona_usage(hours=hours),
        'top_users': monitor.top_users(hours=hours, limit=10),
        'errors': monitor.error_summary(hours=hours, limit=10),
        'timeline': monitor.timeline(hours=hours)
    }
    
    if output_file is None:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = f"activity_report_{ts}.json"
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report exported to {output_file}")
    return report


def cleanup_old_logs(days: int = 90, dry_run: bool = True) -> int:
    """Remove activity logs older than N days.
    
    Args:
        days: Age threshold (default 90)
        dry_run: Show what would be deleted without actually deleting (default True)
    
    Returns:
        Number of rows deleted
    """
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    conn = sqlite3.connect('usage_metrics.sqlite')
    
    # Count rows to delete
    count = conn.execute(
        "SELECT COUNT(*) FROM events WHERE ts < ?", (cutoff,)
    ).fetchone()[0]
    
    if dry_run:
        print(f"Would delete {count} events older than {days} days")
        print(f"Cutoff date: {cutoff}")
        
        # Show sample of what would be deleted
        sample = conn.execute(
            "SELECT ts, user_hash, query_type FROM events WHERE ts < ? LIMIT 5", (cutoff,)
        ).fetchall()
        if sample:
            print("\nSample of rows to delete:")
            for row in sample:
                print(f"  {row[0]} - {row[1]} ({row[2]})")
    else:
        conn.execute("DELETE FROM events WHERE ts < ?", (cutoff,))
        conn.commit()
        print(f"✅ Deleted {count} events older than {days} days")
    
    conn.close()
    return count


def archive_logs(days: int = 90, archive_path: Optional[str] = None) -> str:
    """Archive old logs to a separate SQL file before deletion.
    
    Args:
        days: Age threshold (default 90)
        archive_path: Output file path (default: logs_archive_{timestamp}.sql)
    
    Returns:
        Path to archive file
    """
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    if archive_path is None:
        ts = datetime.utcnow().strftime("%Y%m%d")
        archive_path = f"logs_archive_{ts}.sql"
    
    conn = sqlite3.connect('usage_metrics.sqlite')
    
    # Get rows to archive
    rows = conn.execute(
        "SELECT * FROM events WHERE ts < ? ORDER BY ts", (cutoff,)
    ).fetchall()
    
    # Get column names
    cursor = conn.execute("PRAGMA table_info(events)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Write SQL
    with open(archive_path, 'w') as f:
        f.write("-- Activity logs archive\n")
        f.write(f"-- Generated: {datetime.utcnow().isoformat()}\n")
        f.write(f"-- Events before: {cutoff}\n\n")
        
        for row in rows:
            placeholders = ','.join(['?' for _ in columns])
            col_names = ','.join(columns)
            f.write(f"INSERT INTO events ({col_names}) VALUES ({placeholders});\n")
    
    print(f"✅ Archived {len(rows)} events to {archive_path}")
    conn.close()
    return archive_path


def get_user_activity(user_hash: str, limit: int = 50) -> list:
    """Get all activity for a specific user.
    
    Args:
        user_hash: User ID hash (first 12 chars of SHA256)
        limit: Max events to return
    
    Returns:
        List of events
    """
    conn = sqlite3.connect('usage_metrics.sqlite')
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute(
        "SELECT * FROM events WHERE user_hash = ? ORDER BY ts DESC LIMIT ?",
        (user_hash, limit)
    ).fetchall()
    
    conn.close()
    return [dict(row) for row in rows]


def get_error_distribution() -> dict:
    """Analyze distribution of errors."""
    conn = sqlite3.connect('usage_metrics.sqlite')
    
    errors = conn.execute("""
        SELECT 
            error,
            COUNT(*) as count,
            COUNT(DISTINCT user_hash) as affected_users,
            AVG(latency_ms) as avg_latency
        FROM events
        WHERE success = 0 AND error IS NOT NULL AND error != ''
        GROUP BY error
        ORDER BY count DESC
    """).fetchall()
    
    conn.close()
    
    result = {}
    for error, count, users, latency in errors:
        result[error] = {
            'count': count,
            'affected_users': users,
            'avg_latency_ms': round(latency, 1) if latency else None
        }
    
    return result


def get_slowest_queries(limit: int = 10) -> list:
    """Find slowest successful queries.
    
    Args:
        limit: Number of queries to return
    
    Returns:
        List of slow queries
    """
    conn = sqlite3.connect('usage_metrics.sqlite')
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute("""
        SELECT 
            ts,
            user_hash,
            query_type,
            latency_ms,
            raw_query
        FROM events
        WHERE success = 1
        ORDER BY latency_ms DESC
        LIMIT ?
    """, (limit,)).fetchall()
    
    conn.close()
    return [dict(row) for row in rows]


def get_success_rate_trend(hours: int = 24, interval_hours: int = 1) -> list:
    """Get success rate trend over time.
    
    Args:
        hours: Time window
        interval_hours: Interval size
    
    Returns:
        List of success rates per interval
    """
    conn = sqlite3.connect('usage_metrics.sqlite')
    
    intervals = []
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    for i in range(hours // interval_hours):
        start = cutoff + timedelta(hours=i * interval_hours)
        end = start + timedelta(hours=interval_hours)
        
        total, successes = conn.execute("""
            SELECT 
                COUNT(*),
                SUM(CASE WHEN success=1 THEN 1 ELSE 0 END)
            FROM events
            WHERE ts >= ? AND ts < ?
        """, (start.isoformat(), end.isoformat())).fetchone()
        
        success_rate = (successes / total * 100) if total > 0 else 0
        intervals.append({
            'start': start.isoformat(),
            'end': end.isoformat(),
            'queries': total or 0,
            'success_rate': round(success_rate, 1)
        })
    
    conn.close()
    return intervals


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("📊 PerisAI Bot Monitoring Utilities\n")
        print("Usage:")
        print("  python3 monitor_utils.py export [hours]")
        print("  python3 monitor_utils.py cleanup [days]")
        print("  python3 monitor_utils.py archive [days]")
        print("  python3 monitor_utils.py errors")
        print("  python3 monitor_utils.py slowest [limit]")
        print("  python3 monitor_utils.py trend [hours]")
        print("\nExamples:")
        print("  python3 monitor_utils.py export 24")
        print("  python3 monitor_utils.py cleanup 90")
        print("  python3 monitor_utils.py archive 90")
        print("  python3 monitor_utils.py errors")
        print("  python3 monitor_utils.py slowest 10")
        print("  python3 monitor_utils.py trend 24")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "export":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        report = export_activity_report(hours=hours)
        print(f"Health: {report['health']['last_24h']['success_rate']:.1f}% success")
    
    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        count = cleanup_old_logs(days=days, dry_run=True)
        print("Use --confirm to actually delete")
        if len(sys.argv) > 3 and sys.argv[3] == "--confirm":
            cleanup_old_logs(days=days, dry_run=False)
    
    elif command == "archive":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        path = archive_logs(days=days)
        print(f"Archive ready: {path}")
    
    elif command == "errors":
        errors = get_error_distribution()
        print("Error Distribution:")
        for error, data in list(errors.items())[:10]:
            print(f"  {error[:50]}: {data['count']}x ({data['affected_users']} users)")
    
    elif command == "slowest":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        slow = get_slowest_queries(limit=limit)
        print(f"Top {limit} Slowest Queries:")
        for q in slow:
            print(f"  {q['latency_ms']:.0f}ms - {q['query_type']} - {q['ts']}")
    
    elif command == "trend":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        trend = get_success_rate_trend(hours=hours)
        print(f"Success Rate Trend (Last {hours}h):")
        for interval in trend[-5:]:  # Show last 5 intervals
            bar = "█" * int(interval['success_rate'] / 5)
            print(f"  {interval['start'][11:16]} {bar} {interval['success_rate']:.0f}% ({interval['queries']} q)")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
