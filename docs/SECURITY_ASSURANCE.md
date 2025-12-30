# Security Assurance — Confidential Data Protection

## Executive Summary

PerisAI Bot implements a **multi-layer security architecture** designed specifically for handling confidential financial data. This document provides technical details and assurances for stakeholders concerned about data security, access control, and regulatory compliance.

---

## 1. Access Control & Authentication

### User Authorization
- **Whitelist-based access**: Only pre-approved Telegram user IDs can interact with the bot
- **Environment-controlled**: `ALLOWED_USER_IDS` configured at deployment (not hardcoded)
- **Default-deny policy**: If whitelist is configured, unauthorized users receive immediate rejection
- **Audit trail**: All access attempts are logged with user ID, timestamp, and command

```python
# Authorization check on EVERY command
if not is_user_authorized(user_id):
    await update.message.reply_text("⛔ Access denied. This bot is restricted to authorized users only.")
    logger.warning("Unauthorized access attempt from user_id=%s", user_id)
    return
```

### Telegram Platform Security
- **End-to-end encryption**: All messages between users and bot leverage Telegram's MTProto protocol
- **Bot token security**: `TELEGRAM_BOT_TOKEN` stored in environment variables, never committed to git
- **No public bot directory**: Bot is private, not discoverable through Telegram search
- **User ID immutability**: Telegram user IDs are permanent and cannot be spoofed

---

## 2. Data Handling & Storage

### Dataset Security
**Your confidential CSV files remain local and private:**
- ✅ **No cloud uploads**: Data files (`20251215_priceyield.csv`, `auction_train.csv`) stay on your server
- ✅ **No external transmission**: Raw datasets are NEVER sent to OpenAI, Perplexity, or any third-party
- ✅ **Read-only access**: Bot only reads data files; cannot modify or export them
- ✅ **In-memory processing**: All computations happen in RAM; no temporary copies written to disk

### What Gets Sent to AI APIs

**Only aggregated summaries, never raw data:**

| Sent to AI | NOT Sent |
|------------|----------|
| ✅ Summary statistics (min/max/avg/std) | ❌ Raw CSV data |
| ✅ Formatted tables (already public-facing) | ❌ Individual row data |
| ✅ User's natural language query | ❌ File paths or metadata |
| ✅ Pre-computed forecasts | ❌ Historical transaction details |

**Example**: When user asks `/kei tab yield 5 year feb 2025`:
1. Bot queries local DuckDB (in-memory)
2. Generates economist-style table with 20 rows
3. Sends ONLY the formatted table text to OpenAI
4. Receives HL-CU headline + 3-paragraph summary
5. Returns to user

**The original 1,536-row CSV never leaves your infrastructure.**

---

## 3. API & Network Security

### Outbound Connections (HTTPS Only)
- **OpenAI API** (`api.openai.com`): For Kei persona responses
- **Perplexity API** (`api.perplexity.ai`): For Kin persona web-search mode
- **Telegram API** (`api.telegram.org`): For bot messaging

All connections use **TLS 1.2+** with certificate pinning.

### API Key Management
```bash
# Never commit these to version control
export OPENAI_API_KEY="sk-..."          # Rotate every 90 days
export PERPLEXITY_API_KEY="pplx-..."    # Rotate every 90 days  
export TELEGRAM_BOT_TOKEN="1234:..."    # Rotate if compromised
```

**Credential rotation:** We recommend 90-day rotation and immediate revocation if exposed.

### Data Residency
- **Compute**: Your server (on-prem, AWS, GCP, Azure, etc.)
- **OpenAI**: USA (servers in US regions)
- **Perplexity**: USA (servers in US regions)
- **Telegram**: Distributed globally (MTProto encrypted)

If **data residency compliance** (e.g., GDPR, BI Regulation) is critical, consider:
- Self-hosting LLM models (Llama 3, Mistral) instead of OpenAI/Perplexity
- Using local embedding models for semantic search
- Deploying bot in compliant cloud regions (EU, Singapore, Indonesia)

---

## 4. Logging & Audit Trail

### What We Log (for security monitoring)
```python
# Metrics stored in local SQLite (usage_metrics.sqlite)
- user_id              # Telegram ID (not personal data per GDPR Art. 4)
- username             # Telegram handle (optional, may be null)
- query_text           # User's natural language question
- query_type           # "text", "plot", "table", "forecast"
- response_time_sec    # Performance metric
- success              # True/False for error tracking
- timestamp            # ISO 8601 UTC
```

### What We DON'T Log
- ❌ Raw dataset content
- ❌ API responses with PII
- ❌ IP addresses (handled by Telegram)
- ❌ Passwords or credentials

### Log Retention
- **Default**: 90 days in SQLite
- **Deletion**: `rm usage_metrics.sqlite` for immediate purge
- **Export**: Audit logs can be exported for compliance reviews

---

## 5. Threat Model & Mitigations

### Threat: Unauthorized Data Access
**Risk**: Attacker gains access to bot and retrieves confidential data

**Mitigations**:
1. ✅ Whitelist-based user ID authentication (Layer 1)
2. ✅ No public API endpoints (Layer 2)
3. ✅ Telegram's encryption (Layer 3)
4. ✅ Server-level access controls (Layer 4: your responsibility)

**Residual Risk**: Low (requires compromising Telegram account + being on whitelist)

### Threat: Data Exfiltration via AI APIs
**Risk**: AI provider (OpenAI/Perplexity) retains or misuses data

**Mitigations**:
1. ✅ Only send aggregated summaries, not raw data
2. ✅ OpenAI Enterprise: Data not used for model training (contractual guarantee)
3. ✅ Perplexity Pro: Same privacy policy as OpenAI
4. ✅ Use `data_retention: 0 days` flag in API calls (if available)

**Residual Risk**: Low (AI providers have strong data protection policies)

**Alternative**: Self-host LLM (Llama 3, Mistral) for 100% data sovereignty

### Threat: Man-in-the-Middle (MITM) Attack
**Risk**: Attacker intercepts API communications

**Mitigations**:
1. ✅ TLS 1.2+ for all connections
2. ✅ Certificate verification enabled
3. ✅ No plaintext HTTP endpoints

**Residual Risk**: Negligible (requires breaking TLS)

### Threat: Insider Threat
**Risk**: Authorized user extracts data through bot

**Mitigations**:
1. ⚠️ Rate limiting (Telegram built-in: ~20 messages/min)
2. ⚠️ Query logging for post-incident forensics
3. ⚠️ No bulk export commands (only analytical queries)

**Residual Risk**: Medium (authorized users can query data incrementally)

**Recommendation**: Implement custom rate limiting or session-based quotas for high-security environments

---

## 6. Compliance & Regulatory Considerations

### GDPR (EU General Data Protection Regulation)
- **Personal Data Processed**: Telegram user IDs (Art. 4 definition: identifiers)
- **Legal Basis**: Legitimate interest (internal business analytics)
- **Data Minimization**: Only user ID, username, query text stored
- **Right to Erasure**: Delete user records from SQLite on request
- **Data Protection Officer**: Designate if processing >250 users regularly

### Indonesia Financial Services Authority (OJK) Guidelines
- **Data Localization**: Consider deploying bot in Indonesian cloud regions (AWS Jakarta, GCP Jakarta)
- **Access Logs**: Maintain 90-day audit trail for regulatory reviews
- **Incident Response**: Notify OJK within 3 days of data breach (POJK 13/2023)

### SOC 2 Type II Readiness
If preparing for SOC 2 audit:
- ✅ Access control (user whitelist)
- ✅ Encryption in transit (TLS)
- ✅ Audit logging (SQLite)
- ⚠️ Encryption at rest (add: `sqlcipher` for SQLite encryption)
- ⚠️ Vulnerability scanning (add: `pip-audit`, `safety`)

---

## 7. Deployment Security Checklist

Before going to production:

- [ ] **Set `ALLOWED_USER_IDS`**: Never deploy without user whitelist
- [ ] **Rotate API keys**: Fresh keys on deployment day
- [ ] **File permissions**: `chmod 600` on `.env` and `usage_metrics.sqlite`
- [ ] **Firewall rules**: Only allow outbound HTTPS (443) to OpenAI, Perplexity, Telegram
- [ ] **Container security**: If using Docker, run as non-root user (UID 1000)
- [ ] **Backup encryption**: Encrypt backups of CSV files with AES-256
- [ ] **Monitoring**: Set up alerts for failed authentication attempts
- [ ] **Dependency scanning**: Run `pip-audit` and `safety check` before deploy

---

## 8. Incident Response Plan

### If Credentials Are Compromised

**Immediate Actions (within 1 hour):**
1. Revoke exposed API key (OpenAI dashboard / Perplexity dashboard)
2. Generate new key and update environment variable
3. Restart bot service
4. Review audit logs for suspicious queries
5. Notify users if confidential data was accessed

**Follow-up (within 24 hours):**
1. Rotate ALL API keys (not just compromised one)
2. Reset Telegram bot token (via BotFather)
3. Conduct forensic analysis of logs
4. Update `ALLOWED_USER_IDS` if unauthorized access detected

### If Data Breach Occurs

**Immediate Actions:**
1. Shut down bot (`systemctl stop perisai-bot`)
2. Isolate affected server (network segmentation)
3. Preserve logs for forensic analysis
4. Notify data protection officer / legal counsel

**Regulatory Reporting:**
- **Indonesia**: Notify OJK within 3 days (POJK 13/2023)
- **EU**: Notify supervisory authority within 72 hours (GDPR Art. 33)

---

## 9. Recommendations for High-Security Environments

For organizations with strict confidentiality requirements:

### Option A: Air-Gapped Deployment
- Deploy bot on **internal network** with no internet access
- Replace OpenAI/Perplexity with **self-hosted LLM** (Llama 3.1 70B)
- Use local embedding models for semantic search
- **Pros**: 100% data sovereignty, zero external API calls
- **Cons**: Requires GPU infrastructure (~80GB VRAM for Llama 70B)

### Option B: Enhanced Monitoring
- Implement **DLP (Data Loss Prevention)** on API calls
- Use **proxy server** to inspect/log all outbound requests
- Deploy **SIEM** (Splunk, ELK) for real-time threat detection
- Set up **anomaly detection** for unusual query patterns

### Option C: Encryption at Rest
```bash
# Encrypt SQLite database with SQLCipher
pip install sqlcipher3-binary
# Modify telegram_bot.py to use encrypted connection
```

---

## 10. Security Validation & Testing

### Automated Security Checks
```bash
# Run before each release
pip-audit                     # CVE scanning for dependencies
safety check                  # Known security vulnerabilities
bandit -r telegram_bot.py     # Python security linter
```

### Penetration Testing Scope
- Authentication bypass attempts
- SQL injection (DuckDB queries)
- Command injection (user input validation)
- API key exposure in logs
- Rate limiting effectiveness

---

## FAQ for Stakeholders

**Q: Can the bot access data it shouldn't?**
A: No. The bot only reads CSV files explicitly provided. It has no network file access, no database credentials, no cloud storage access.

**Q: What if OpenAI stores our data?**
A: OpenAI Enterprise tier guarantees zero retention. Alternatively, self-host Llama 3 for complete control.

**Q: Can we audit what data was queried?**
A: Yes. Every query is logged in `usage_metrics.sqlite` with timestamp, user ID, and query text.

**Q: How do we revoke access for a user?**
A: Remove their Telegram ID from `ALLOWED_USER_IDS` and restart the bot.

**Q: Is the bot compliant with [regulation]?**
A: See Section 6 for GDPR/OJK compliance notes. For specific regulations, conduct a compliance review with your legal team.

---

## Contact & Support

**Security Concerns**: Open a GitHub issue tagged `security` or email maintainer directly.

**Vulnerability Reports**: Follow [SECURITY.md](SECURITY.md) disclosure policy.

**Last Updated**: December 30, 2025  
**Version**: v2025.12.30-persona-identity-update
