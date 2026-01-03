"""Bot metrics and traffic tracking."""
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any

import usage_store

class BotMetrics:
    """Track bot activity and performance metrics."""
    
    def __init__(self):
        self.queries: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
    
    def log_query(self, user_id: int, username: str, query: str, query_type: str, 
                  response_time: float, success: bool, error: str = None, 
                  persona: str = "unknown"):
        """Log a user query."""
        self.queries.append({
            "timestamp": datetime.now(),
            "user_id": user_id,
            "username": username,
            "query": query[:100],  # Truncate long queries
            "query_type": query_type,
            "persona": persona,
            "response_time_ms": round(response_time * 1000, 2),
            "success": success,
            "error": error
        })
        try:
            usage_store.log_event(
                user_id=user_id,
                username=username,
                query=query,
                query_type=query_type,
                persona=persona,
                response_time_ms=round(response_time * 1000, 2),
                success=success,
                error=error,
            )
        except Exception as exc:  # pragma: no cover
            logging.getLogger("metrics").debug(f"usage_store log_event failed: {exc}")
    
    def log_error(self, endpoint: str, error: str, user_id: int = None):
        """Log an error."""
        self.errors.append({
            "timestamp": datetime.now(),
            "endpoint": endpoint,
            "error": str(error)[:200],
            "user_id": user_id
        })
        try:
            usage_store.log_error(endpoint, str(error), user_id=user_id)
        except Exception as exc:  # pragma: no cover
            logging.getLogger("metrics").debug(f"usage_store log_error failed: {exc}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        uptime = datetime.now() - self.start_time
        
        # Query stats
        total_queries = len(self.queries)
        successful_queries = sum(1 for q in self.queries if q["success"])
        failed_queries = total_queries - successful_queries
        
        # User stats
        unique_users = len(set(q["user_id"] for q in self.queries))
        user_query_counts = defaultdict(int)
        for q in self.queries:
            user_query_counts[q["user_id"]] += 1
        
        # Response time stats
        if self.queries:
            response_times = [q["response_time_ms"] for q in self.queries if q["success"]]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            min_response_time = min(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
        else:
            avg_response_time = min_response_time = max_response_time = 0
        
        # Query type breakdown
        query_types = defaultdict(int)
        for q in self.queries:
            query_types[q["query_type"]] += 1
        
        # Persona breakdown
        personas = defaultdict(int)
        for q in self.queries:
            personas[q["persona"]] += 1
        
        # Last 10 queries
        recent_queries = [
            {
                "time": q["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "user": f"{q['username']} ({q['user_id']})",
                "query": q["query"],
                "type": q["query_type"],
                "persona": q["persona"],
                "response_ms": q["response_time_ms"],
                "success": q["success"],
                "error": q["error"]
            }
            for q in self.queries[-10:]
        ]
        
        # Last 5 errors
        recent_errors = [
            {
                "time": e["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "endpoint": e["endpoint"],
                "error": e["error"],
                "user_id": e["user_id"]
            }
            for e in self.errors[-5:]
        ]
        
        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_readable": str(uptime).split(".")[0],
            "queries": {
                "total": total_queries,
                "successful": successful_queries,
                "failed": failed_queries,
                "success_rate": f"{(successful_queries/total_queries*100):.1f}%" if total_queries > 0 else "N/A"
            },
            "users": {
                "unique": unique_users,
                "top_users": sorted(user_query_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            "performance": {
                "avg_response_ms": round(avg_response_time, 2),
                "min_response_ms": round(min_response_time, 2),
                "max_response_ms": round(max_response_time, 2)
            },
            "query_types": dict(query_types),
            "personas": dict(personas),
            "recent_queries": recent_queries,
            "recent_errors": recent_errors,
            "errors_total": len(self.errors)
        }
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get stats for a specific user."""
        user_queries = [q for q in self.queries if q["user_id"] == user_id]
        if not user_queries:
            return {"user_id": user_id, "queries": 0}
        
        successful = sum(1 for q in user_queries if q["success"])
        response_times = [q["response_time_ms"] for q in user_queries if q["success"]]
        
        query_types = defaultdict(int)
        for q in user_queries:
            query_types[q["query_type"]] += 1
        
        return {
            "user_id": user_id,
            "username": user_queries[0]["username"],
            "total_queries": len(user_queries),
            "successful": successful,
            "failed": len(user_queries) - successful,
            "avg_response_ms": round(sum(response_times) / len(response_times), 2) if response_times else 0,
            "query_types": dict(query_types),
            "last_query": user_queries[-1]["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def get_html_dashboard(self) -> str:
        """Return an HTML dashboard view of metrics."""
        stats = self.get_stats()
        
        # Format uptime
        uptime = stats["uptime_readable"]
        
        # Build HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Bot Traffic Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; border-left: 4px solid #007bff; padding-left: 10px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 28px; font-weight: bold; color: #007bff; }}
        .stat-label {{ font-size: 12px; color: #666; text-transform: uppercase; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; margin: 20px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th {{ background: #007bff; color: white; padding: 12px; text-align: left; font-weight: 600; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .success {{ color: #28a745; font-weight: 600; }}
        .error {{ color: #dc3545; }}
        .time {{ color: #666; font-size: 12px; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }}
        .badge-plot {{ background: #e3f2fd; color: #1976d2; }}
        .badge-text {{ background: #f3e5f5; color: #7b1fa2; }}
        .badge-kei {{ background: #fff3e0; color: #f57c00; }}
        .badge-kin {{ background: #e0f2f1; color: #00796b; }}
        .badge-both {{ background: #fce4ec; color: #c2185b; }}
        .metric-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
        .metric-row:last-child {{ border-bottom: none; }}
        .metric-label {{ color: #666; }}
        .metric-value {{ font-weight: 600; color: #333; }}
        .empty {{ text-align: center; color: #999; padding: 40px; }}
        .header-info {{ color: #666; font-size: 14px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Perisai Bot Traffic Dashboard</h1>
        <div class="header-info">Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Uptime: {uptime}</div>
        
        <h2>📊 Overall Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['queries']['total']}</div>
                <div class="stat-label">Total Queries</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #28a745;">{stats['queries']['successful']}</div>
                <div class="stat-label">Successful</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #dc3545;">{stats['queries']['failed']}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['queries']['success_rate']}</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['users']['unique']}</div>
                <div class="stat-label">Unique Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['errors_total']}</div>
                <div class="stat-label">Errors</div>
            </div>
        </div>
        
        <h2>⚡ Performance Metrics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['performance']['avg_response_ms']}</div>
                <div class="stat-label">Avg Response Time (ms)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['performance']['min_response_ms']}</div>
                <div class="stat-label">Min Response Time (ms)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['performance']['max_response_ms']}</div>
                <div class="stat-label">Max Response Time (ms)</div>
            </div>
        </div>
        
        <h2>👥 Top Users</h2>
        <table>
            <thead>
                <tr>
                    <th>User ID</th>
                    <th>Username</th>
                    <th>Queries</th>
                </tr>
            </thead>
            <tbody>
"""
        if stats['users']['top_users']:
            for user_id, count in stats['users']['top_users']:
                html += f"                <tr><td>{user_id}</td><td>{count}</td></tr>\n"
        else:
            html += "                <tr><td colspan='3' class='empty'>No users yet</td></tr>\n"
        
        html += """            </tbody>
        </table>
        
        <h2>📈 Query Breakdown</h2>
        <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
"""
        for query_type, count in stats['query_types'].items():
            percentage = (count / stats['queries']['total'] * 100) if stats['queries']['total'] > 0 else 0
            html += f"""            <div class="metric-row">
                <span class="metric-label"><span class="badge badge-{query_type.lower()}">{query_type.upper()}</span></span>
                <span class="metric-value">{count} queries ({percentage:.1f}%)</span>
            </div>
"""
        html += "        </div>\n"
        
        html += """        <h2>🎭 Persona Usage</h2>
        <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
"""
        for persona, count in stats['personas'].items():
            percentage = (count / stats['queries']['total'] * 100) if stats['queries']['total'] > 0 else 0
            html += f"""            <div class="metric-row">
                <span class="metric-label"><span class="badge badge-{persona.lower()}">{persona.upper()}</span></span>
                <span class="metric-value">{count} queries ({percentage:.1f}%)</span>
            </div>
"""
        html += "        </div>\n"
        
        html += """        <h2>📝 Recent Queries (Last 10)</h2>
        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>User</th>
                    <th>Query</th>
                    <th>Type</th>
                    <th>Persona</th>
                    <th>Response (ms)</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""
        if stats['recent_queries']:
            for q in reversed(stats['recent_queries']):
                status = '<span class="success">✓ OK</span>' if q['success'] else f'<span class="error">✗ {q["error"]}</span>'
                html += f"""                <tr>
                    <td class="time">{q['time']}</td>
                    <td>{q['user']}</td>
                    <td title="{q['query']}">{q['query'][:50]}...</td>
                    <td><span class="badge badge-{q['type'].lower()}">{q['type'].upper()}</span></td>
                    <td><span class="badge badge-{q['persona'].lower()}">{q['persona'].upper()}</span></td>
                    <td>{q['response_ms']}</td>
                    <td>{status}</td>
                </tr>
"""
        else:
            html += "                <tr><td colspan='7' class='empty'>No queries yet</td></tr>\n"
        
        html += """            </tbody>
        </table>
        
        <h2>⚠️ Recent Errors (Last 5)</h2>
        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Endpoint</th>
                    <th>Error</th>
                    <th>User ID</th>
                </tr>
            </thead>
            <tbody>
"""
        if stats['recent_errors']:
            for e in reversed(stats['recent_errors']):
                html += f"""                <tr>
                    <td class="time">{e['time']}</td>
                    <td>{e['endpoint']}</td>
                    <td><span class="error">{e['error']}</span></td>
                    <td>{e['user_id'] or 'N/A'}</td>
                </tr>
"""
        else:
            html += "                <tr><td colspan='4' class='empty'>No errors yet</td></tr>\n"
        
        html += """            </tbody>
        </table>
    </div>
</body>
</html>
"""
        return html

# Global metrics instance
metrics = BotMetrics()
