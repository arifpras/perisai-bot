"""Bot metrics and traffic tracking."""
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any

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
    
    def log_error(self, endpoint: str, error: str, user_id: int = None):
        """Log an error."""
        self.errors.append({
            "timestamp": datetime.now(),
            "endpoint": endpoint,
            "error": str(error)[:200],
            "user_id": user_id
        })
    
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

# Global metrics instance
metrics = BotMetrics()
