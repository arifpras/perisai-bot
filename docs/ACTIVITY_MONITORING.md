# 📊 User Activity Monitoring

PerisAI Bot includes built-in activity monitoring that tracks all user interactions, query patterns, and system performance.

## Overview

The monitoring system logs:
- **User Queries**: Every user request with response time and success status
- **Query Types**: Data queries, forecasts, aggregations, AI interactions
- **Personas**: Kei (quantitative) vs Kin (strategic) usage
- **Errors**: Failed queries with error messages for debugging
- **Performance**: Response latency in milliseconds

All data is stored in **SQLite** (`usage_metrics.sqlite`) without external dependencies.

## Features

### 1. Automatic Logging
Every user query is automatically logged when they:
- Ask `/kei`, `/kin`, or `/both` commands
- Use bond data queries (yield, price, forecasts)
- Generate charts or statistics

Logged fields:
```
- Timestamp (UTC)
- User ID (hashed)
- Username
- Query text
- Query type (point_query, range_query, forecast_query, etc.)
- Persona (kei, kin, default)
- Response time (ms)
- Success/Failure status
- Error message (if failed)
```

### 2. Dashboard Command

**Admin users only** can view activity stats:

```bash
/activity
```

Shows:
- **Health Status**: Total queries, success rate, avg response time, unique users
- **Query Breakdown**: Count and success rate by query type
- **Top Users**: Most active users and their success rates
- **Recent Errors**: Common error types in last 24 hours

Example output:
```
📊 PerisAI Bot Activity (Last 24h)

Health Status
  Queries: 245 (96% success)
  Latency: 1250 ms
  Users: 12 (weekly: 28)

Query Types
  point_query: 156 (98%)
  range_query: 45 (95%)
  forecast_query: 28 (89%)
  kei_query: 14 (100%)

Top Users
  @arifpras: 85 queries (98%)
  @trader_x: 52 queries (94%)
  @analyst_y: 38 queries (92%)

Recent Errors
  ✅ None
```

### 3. Command-Line Monitor

Run the activity monitor script for detailed reports:

```bash
python3 activity_monitor.py
```

Generates a formatted dashboard with:
- Bot health metrics (24h and 7d windows)
- Query type statistics with success rates
- Persona usage breakdown (Kei vs Kin)
- Timeline view (queries per hour)
- Top active users
- Recent error tracking

Example output:
```
================================================================================
📊 PerisAI Bot Activity Monitor
================================================================================

🏥 Bot Health (Last 24 Hours)
  Total Queries    : 245
  Successful       : 235 (96.0%)
  Failed           : 10
  Avg Response     : 1250.5 ms
  Unique Users     : 12
  Weekly Users     : 28

📈 Query Types
Type            | Count | Success % | Avg Latency
point_query     |   156 |       98% | 850.3ms
range_query     |    45 |       95% | 1200.0ms
forecast_query  |    28 |       89% | 2100.5ms
kei_query       |    14 |      100% | 800.0ms

🎭 Persona Usage
Persona     | Queries | Success % | Latency
default     |     156 |       98% | 850.3ms
kei         |      89 |       95% | 1150.0ms
kin         |      28 |      100% | 1050.0ms

👥 Most Active Users
User            | Queries | Success % | Latency
arifpras        |      85 |       98% | 1050.3ms
trader_x        |      52 |       94% | 1200.0ms
analyst_y       |      38 |       92% | 1350.5ms

⚠️ Recent Errors
  ✅ No errors in last 24 hours!

📅 Activity Timeline (Last 24 Hours)
  2024-12-26 08:00:00 ████ (8 queries, 100% success)
  2024-12-26 09:00:00 ██████████ (20 queries, 98% success)
  2024-12-26 10:00:00 ████████ (16 queries, 94% success)
```

## Configuration

### Admin Access

Set the admin user ID to enable `/activity` command:

```bash
export ADMIN_USER_ID="YOUR_TELEGRAM_USER_ID"
```

Only this user can view activity statistics.

### Database Path

By default, logs are stored in `usage_metrics.sqlite` in the bot directory.

Override with:
```bash
export USAGE_DB_PATH="/path/to/usage_metrics.sqlite"
```

## Database Schema

### events table

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,              -- ISO 8601 timestamp (UTC)
    persona TEXT,                  -- 'kei', 'kin', 'default'
    query_type TEXT,               -- 'point_query', 'range_query', 'forecast_query', etc.
    success INTEGER,               -- 0 = failed, 1 = succeeded
    latency_ms REAL,              -- Response time in milliseconds
    user_hash TEXT,               -- SHA256 hash of user ID (first 12 chars)
    username TEXT,                -- Telegram username
    error TEXT,                   -- Error message if failed (max 200 chars)
    raw_query TEXT                -- Original user query (max 200 chars)
);
```

Indexes:
- `idx_events_ts`: Fast queries by timestamp
- `idx_events_persona`: Fast queries by persona

## Query Examples

### Monitor Health (Last 24 Hours)

```python
from activity_monitor import ActivityMonitor
monitor = ActivityMonitor()
health = monitor.health_check()
print(f"Success Rate: {health['last_24h']['success_rate']:.1f}%")
print(f"Avg Latency: {health['last_24h']['avg_latency_ms']} ms")
```

### Get Error Summary

```python
errors = monitor.error_summary(hours=24, limit=10)
for error in errors:
    print(f"{error['error']}: {error['count']} occurrences")
```

### Analyze User Patterns

```python
users = monitor.top_users(hours=24, limit=5)
for user in users:
    print(f"@{user['username']}: {user['query_count']} queries")
```

### Track Query Types

```python
stats = monitor.query_stats(hours=24)
for qtype, data in stats.items():
    print(f"{qtype}: {data['count']} ({data['success_rate']:.1f}% success)")
```

## Privacy & Security

### User Privacy
- User IDs are hashed using SHA256 (irreversible)
- Only hashed IDs are stored in the database
- Usernames are stored for convenience (max 80 chars)

### Data Retention
- All events are stored indefinitely
- Consider implementing periodic cleanup for GDPR compliance:

```python
# Delete events older than 90 days
import sqlite3
from datetime import datetime, timedelta

cutoff = (datetime.utcnow() - timedelta(days=90)).isoformat()
conn = sqlite3.connect('usage_metrics.sqlite')
conn.execute("DELETE FROM events WHERE ts < ?", (cutoff,))
conn.commit()
conn.close()
```

### Query Text
- Raw queries are truncated to 200 characters
- Sensitive information should not be included in queries

## Integration with Render.com

Activity logs persist across deployments:

1. **Local development**: Logs stored in `usage_metrics.sqlite`
2. **Render.com deployment**: Use persistent filesystem or upload logs periodically
3. **Monitoring**: View `/activity` command in Telegram for real-time stats

## Troubleshooting

### No data showing in /activity

1. Check that `ADMIN_USER_ID` environment variable is set
2. Verify you're using the correct admin user ID
3. Wait for queries to complete (events logged on success)

### Database size growing too fast

Use periodic cleanup (see Privacy section) or:

```bash
# Archive logs monthly
sqlite3 usage_metrics.sqlite ".dump events" > events_2024_12.sql
sqlite3 usage_metrics.sqlite "DELETE FROM events WHERE ts < '2024-11-01'"
```

### Activity monitor script shows no data

1. Ensure bot has been running and receiving queries
2. Check that `usage_metrics.sqlite` exists in the correct directory
3. Verify database read permissions: `chmod 644 usage_metrics.sqlite`

## Future Enhancements

Planned monitoring features:
- **Export APIs**: CSV/JSON export of activity logs
- **Alerting**: Notifications for error spikes or anomalies
- **Cost Tracking**: Monitor API call costs (OpenAI tokens, etc.)
- **Performance Profiling**: Per-function timing analysis
- **Compliance Reporting**: GDPR/audit trail generation
- **Web Dashboard**: Real-time web interface for activity monitoring
