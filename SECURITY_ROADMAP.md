# Security Roadmap

## Current State
- ✅ SQL injection protection (parameterized queries via DuckDB)
- ✅ Telegram bot user ID authorization
- ❌ API endpoints completely unprotected (no authentication)
- ❌ No rate limiting
- ❌ No audit logging
- ❌ Data in plaintext CSV files on disk
- ❌ No encryption in transit (HTTP only)

## Planned Improvements (Priority Order)

### Phase 1: Authentication & Access Control (HIGH PRIORITY)
**Status**: Not Started
**Effort**: 2-3 days

#### 1.1 API Key Authentication
- Add FastAPI security dependency (`APIKey` or Bearer token)
- Require `X-API-Key` header or `Authorization: Bearer <token>` for all `/query`, `/chat`, `/plot` endpoints
- Load API keys from environment variable or config file
- Reject requests without valid key with 401 Unauthorized

#### 1.2 Rate Limiting per API Key
- Integrate `slowapi` or similar library
- Limit: 10 requests/minute per key, 100 requests/hour per key
- Return 429 Too Many Requests when exceeded
- Track per-key limits in memory or Redis

#### 1.3 Audit Logging
- Log all data access: timestamp, API key/user, query type, data accessed, IP address
- Store logs in rotating file or centralized log service
- Include: query text, tenor, series, date range, returned record count
- Retention: 90 days minimum

### Phase 2: Data Protection (HIGH PRIORITY)
**Status**: Not Started
**Effort**: 3-5 days

#### 2.1 Data Classification & Masking
- Mark sensitive columns in CSV (e.g., price, yield as confidential)
- Implement field-level access control: certain API keys can access certain columns only
- Mask non-essential data in responses (e.g., round yields to 2 decimals if not authorized)

#### 2.2 Encryption at Rest
- Encrypt CSV files using AES-256 (python cryptography library)
- Store encryption key in secure environment variable or vault
- Decrypt on startup (still in-memory, but file is protected)
- Consider moving to PostgreSQL with encrypted columns for larger datasets

#### 2.3 Encryption in Transit
- Enforce HTTPS only in production
- Add HSTS header (Strict-Transport-Security)
- Disable HTTP in production (only allow via reverse proxy with HTTPS termination)

### Phase 3: Query Validation (MEDIUM PRIORITY)
**Status**: Not Started
**Effort**: 2 days

#### 3.1 Query Size Limits
- Limit maximum records returned per query (e.g., 10,000)
- Reject date ranges > 5 years
- Prevent export of entire dataset in single query

#### 3.2 User Intent Validation
- Log suspicious query patterns (bulk exports, repeated identical queries, unusual date ranges)
- Alert on anomalies
- Block if threshold exceeded

### Phase 4: Monitoring & Compliance (MEDIUM PRIORITY)
**Status**: Not Started
**Effort**: 2-3 days

#### 4.1 Security Monitoring
- Add metrics: requests per key, rejected requests, audit log events
- Dashboard to track API usage patterns
- Email alerts for suspicious activity

#### 4.2 Data Governance
- Document data ownership and sensitivity levels
- Create data access policy document
- Compliance checklist (if applicable: GDPR, SOX, internal policies)

## Implementation Plan

### Sprint 1 (Next 2 weeks)
- [ ] Implement Phase 1.1 (API Key auth)
- [ ] Implement Phase 1.2 (rate limiting)
- [ ] Test with Postman/curl

### Sprint 2 (Following 2 weeks)
- [ ] Implement Phase 1.3 (audit logging)
- [ ] Implement Phase 2.1 (data classification)
- [ ] Create access control config

### Sprint 3+ (Future)
- [ ] Phase 2.2 (encryption at rest)
- [ ] Phase 2.3 (enforce HTTPS)
- [ ] Phase 3 (query validation)
- [ ] Phase 4 (monitoring)

## Files to Modify
- `app_fastapi.py` - Add auth middleware, rate limiting, audit logging
- `requirements.txt` - Add `slowapi`, `python-jose`, `cryptography` as needed
- `.env.example` - Add API_KEYS, ENCRYPTION_KEY, LOG_LEVEL
- `priceyield_20251223.py` - Add field-level access control
- New: `security_config.py` - Centralized auth/encryption logic
- New: `audit_log.py` - Audit logging implementation
- New: `SECURITY_POLICY.md` - Data access policy documentation

## Dependencies to Add
```
slowapi>=0.1.9              # Rate limiting
python-jose[cryptography]   # JWT/Bearer tokens
cryptography>=41.0.0        # Field encryption
python-dotenv>=1.0.0        # Env var management
```

## Testing Strategy
- Unit tests for auth middleware (valid/invalid keys)
- Rate limiting tests (verify 429 after threshold)
- Audit logging tests (verify logs written correctly)
- Integration tests with real API endpoints
- Load test to confirm rate limiting works at scale

## Deployment Considerations
- API keys must be rotated periodically (recommend quarterly)
- Encryption keys stored in secure vault (not git, not plaintext env)
- Logs must be rotated and archived (90-day retention)
- HTTPS certificate auto-renewal (if using LetsEncrypt)
- Monitor for security updates to dependencies (weekly)

## Future Considerations
- Move to PostgreSQL for better access control and audit trail
- Implement OAuth2 for user-specific access (vs global API keys)
- Add IP whitelisting for additional layer
- Consider AWS Secrets Manager or HashiCorp Vault for key management
- Implement data residency compliance if needed
