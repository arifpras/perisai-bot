# Security Policy

## Supported Versions

The following versions of PerisAI Bot are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2025.12.x (latest) | :white_check_mark: |
| 2025.11.x | :x:                |
| < 2025.11 | :x:                |

**Note**: We follow a rolling release model. Only the latest stable version receives security patches.

## Reporting a Vulnerability

We take the security of PerisAI Bot seriously. If you discover a security vulnerability, please follow these steps:

### 1. Where to Report
- **Email**: Send detailed vulnerability reports to the repository maintainer
- **GitHub Security**: Use GitHub's private vulnerability reporting feature (preferred)
- **Do NOT**: Create public GitHub issues for security vulnerabilities

### 2. What to Include
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact and severity assessment
- Suggested fix (if available)
- Your contact information for follow-up

### 3. Response Timeline
- **Initial Response**: Within 48 hours of report
- **Status Update**: Every 7 days until resolution
- **Patch Release**: Target within 30 days for critical vulnerabilities

### 4. Disclosure Policy
- We follow coordinated disclosure practices
- Security advisories will be published after patches are available
- We will credit reporters in security advisories (unless anonymity is requested)

### 5. Out of Scope
The following are generally considered out of scope:
- Social engineering attacks
- Physical access attacks
- Denial of Service (DoS) attacks against the bot
- Rate limiting issues (unless they lead to resource exhaustion)

### 6. Encryption & Data Protection
- All API keys and tokens must be stored in environment variables
- No hardcoded credentials in source code
- Sensitive data should not be logged
- Use HTTPS for all external API communications

## Security Best Practices for Deployment

When deploying PerisAI Bot:

1. **Environment Variables**: Set `ALLOWED_USER_IDS` to restrict access
2. **API Keys**: Rotate keys regularly (OPENAI_API_KEY, PERPLEXITY_API_KEY, TELEGRAM_BOT_TOKEN)
3. **Database**: Ensure SQLite database has appropriate file permissions
4. **Logging**: Review logs regularly for suspicious activity patterns
5. **Updates**: Keep dependencies up to date (`pip install --upgrade -r requirements.txt`)

## Known Security Considerations

- **User Authorization**: The bot implements user ID-based authorization via `ALLOWED_USER_IDS`
- **Rate Limiting**: Telegram's built-in rate limits protect against abuse
- **Data Storage**: Usage metrics are stored locally in SQLite (`usage_metrics.sqlite`)
- **API Dependencies**: Security depends on OpenAI, Perplexity, and Telegram API security

## Contact

For security concerns that don't require private disclosure, you may:
- Open a discussion on GitHub
- Tag issues with the `security` label

Thank you for helping keep PerisAI Bot secure!
