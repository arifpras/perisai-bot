# 🎯 Quick Start: User Activity Monitoring

## For Admins

### View Activity in Telegram

```
/activity
```

**Shows (last 24 hours):**
- Total queries & success rate
- Response time (avg latency)
- Number of active users
- Query breakdown by type
- Top 3 most active users
- Recent errors (if any)

**Requirements:** Set `ADMIN_USER_ID` environment variable

```bash
export ADMIN_USER_ID="YOUR_TELEGRAM_USER_ID"
```

### View Detailed Dashboard (CLI)

```bash
python3 activity_monitor.py
```

**Shows:**
- Bot health metrics (24h & 7d)
- Query types (count, success %, latency)
- Persona usage (Kei vs Kin)
- Top 5 users
- Activity timeline (queries per hour)
- Recent errors summary

## For Developers

### Query Activity Data

```python
from activity_monitor import ActivityMonitor

monitor = ActivityMonitor()

# Overall health
health = monitor.health_check()
print(f"Success rate: {health['last_24h']['success_rate']}%")

# By query type
stats = monitor.query_stats(hours=24)
for qtype, data in stats.items():
    print(f"{qtype}: {data['count']} ({data['success_rate']:.0f}%)")

# Top users
users = monitor.top_users(hours=24, limit=10)

# Errors
errors = monitor.error_summary(hours=24, limit=5)

# Persona breakdown
personas = monitor.persona_usage(hours=24)

# Hourly timeline
timeline = monitor.timeline(hours=24)
```

### Raw Database Access

```python
import sqlite3

conn = sqlite3.connect('usage_metrics.sqlite')
conn.row_factory = sqlite3.Row

# Find all queries by specific user
user_hash = 'abc123def456'  # SHA256 of user ID (first 12 chars)
rows = conn.execute(
    "SELECT * FROM events WHERE user_hash = ? ORDER BY ts DESC",
    (user_hash,)
).fetchall()

# Count errors by type
errors = conn.execute("""
    SELECT error, COUNT(*) as count
    FROM events
    WHERE success = 0
    GROUP BY error
    ORDER BY count DESC
""").fetchall()

conn.close()
```

## Data Logged

**Every query logs:**
- ✅ Timestamp (UTC)
- ✅ User (ID hash + username)
- ✅ Query text (first 200 chars)
- ✅ Query type (point, range, forecast, kei_query, etc.)
- ✅ Persona (kei, kin, default)
- ✅ Response time (ms)
- ✅ Success/failure status
- ✅ Error message (if failed, first 200 chars)

## Example: Monitor Query Performance

```python
from activity_monitor import ActivityMonitor
from datetime import datetime, timedelta

monitor = ActivityMonitor()

# Check if bot is healthy
health = monitor.health_check()
last_24h = health['last_24h']

print(f"Queries: {last_24h['total_queries']}")
print(f"Success: {last_24h['success_rate']:.1f}%")
print(f"Latency: {last_24h['avg_latency_ms']} ms")
print(f"Users: {last_24h['unique_users']}")

# Alert if too slow
if last_24h['avg_latency_ms'] > 2000:
    print("⚠️ SLOW: Average response > 2 seconds")

# Alert if too many errors
if last_24h['success_rate'] < 90:
    print("⚠️ ERRORS: Success rate < 90%")
```

## Example: Export Activity Report

```python
from activity_monitor import ActivityMonitor
import json
from datetime import datetime

monitor = ActivityMonitor()
health = monitor.health_check()
stats = monitor.query_stats(hours=24)
users = monitor.top_users(hours=24)

report = {
    'generated': datetime.utcnow().isoformat(),
    'health': health,
    'query_stats': stats,
    'top_users': users
}

with open('activity_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print("Report saved to activity_report.json")
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `/activity` returns "Access denied" | Set `ADMIN_USER_ID` env var with correct user ID |
| No data in dashboard | Wait for queries to complete, check `usage_metrics.sqlite` exists |
| Database file not found | Run bot once to create it, check `USAGE_DB_PATH` env var |
| Slow dashboard script | Database is large, consider archiving old logs |

## Privacy & Compliance

- **User IDs**: Hashed (SHA256, irreversible) - cannot identify users from database
- **Usernames**: Stored for convenience, not required
- **Queries**: Truncated to 200 chars, no sensitive data
- **Retention**: Store indefinitely (implement cleanup per GDPR if needed)

### Delete old logs (example: 90 days)

```python
import sqlite3
from datetime import datetime, timedelta

cutoff = (datetime.utcnow() - timedelta(days=90)).isoformat()
conn = sqlite3.connect('usage_metrics.sqlite')
conn.execute("DELETE FROM events WHERE ts < ?", (cutoff,))
conn.commit()
conn.close()
print("Old logs deleted")
```

## Next Steps

1. ✅ **Enable monitoring**: Bot automatically logs all queries
2. ✅ **Set admin ID**: `export ADMIN_USER_ID="YOUR_ID"`
3. ✅ **View stats**: `/activity` in Telegram or `python3 activity_monitor.py`
4. 📋 **Analyze patterns**: Use `ActivityMonitor` class for custom analysis
5. 🔐 **Archive logs**: Implement retention policy as needed

---

📖 See [ACTIVITY_MONITORING.md](ACTIVITY_MONITORING.md) for complete documentation.
