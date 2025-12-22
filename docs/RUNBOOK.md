# Operational Runbook

## Agentic AI Log Analysis System v1.0

This runbook provides operational procedures for deploying, running, monitoring, and troubleshooting the Agentic AI Log Analysis System.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Configuration](#configuration)
4. [Running the System](#running-the-system)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)
8. [Emergency Procedures](#emergency-procedures)

---

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Python**: 3.11 or higher
- **Memory**: Minimum 2GB RAM, 4GB recommended
- **Disk**: 1GB free space for logs and temporary files
- **Network**: Outbound access to Elasticsearch, SMTP server, and OpenAI API

### External Dependencies
- **Elasticsearch**: Version 8.x, accessible via network
- **Filebeat**: Configured to send ECS-formatted logs to Elasticsearch
- **SMTP Server**: Gmail, Office365, or custom SMTP with TLS support
- **OpenAI API**: Active API key with GPT-4 access

---

## Initial Setup

### 1. Clone and Navigate

```bash
cd c:\Users\sgazanfar\AI-Logs-analysis
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -c "import elasticsearch; import openai; print('Dependencies OK')"
```

---

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Elasticsearch Configuration
ES_HOST=your-elasticsearch-host.com
ES_PORT=9200
ES_USERNAME=elastic
ES_PASSWORD=your-secure-password
ES_INDEX_PATTERN=filebeat-*
ES_USE_SSL=true

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=2000

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_USE_TLS=true
ALERT_RECIPIENTS=team@company.com,oncall@company.com

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/agentic_log_analysis.log

# Analysis Configuration
DEFAULT_ANALYSIS_HOURS=24
MAX_LOGS_PER_RUN=100000
```

### 2. Configuration Files

Ensure the following files are properly configured:

- `config/elasticsearch.yaml` - Elasticsearch connection and query settings
- `config/ai.yaml` - AI provider settings and prompts
- `config/smtp.yaml` - Email server and formatting settings

### 3. Validate Configuration

```bash
python utils/helpers.py --validate-config
```

---

## Running the System

### Daily Scheduled Analysis

The system runs automatically on a daily schedule. To start the scheduler:

```bash
python orchestrator/orchestrator.py --mode scheduled
```

This will:
- Run analysis every day at the configured time (default: 2:00 AM)
- Analyze logs from the past 24 hours
- Send email alerts if issues are found
- Log all activities

### Manual On-Demand Analysis

For immediate analysis:

```bash
# Analyze last 24 hours
python orchestrator/orchestrator.py --mode manual --hours 24

# Analyze last 6 hours
python orchestrator/orchestrator.py --mode manual --hours 6

# Analyze specific time range
python orchestrator/orchestrator.py --mode manual \
  --start "2025-12-17T00:00:00" \
  --end "2025-12-17T23:59:59"

# Analyze with specific filters
python orchestrator/orchestrator.py --mode manual \
  --hours 24 \
  --service "api-gateway" \
  --severity "error,critical"
```

### Running Individual Agents

For testing or debugging:

```bash
# Test log fetcher
python agents/log_fetcher_agent.py --test

# Test error parser
python agents/error_parser_agent.py --test

# Test RCA analyzer
python agents/rca_analyzer_agent.py --test

# Test solution generator
python agents/solution_gen_agent.py --test

# Test email sender
python agents/email_sender_agent.py --test
```

---

## Monitoring

### Log Files

All execution logs are written to:
- **Location**: `logs/agentic_log_analysis.log`
- **Format**: Structured JSON
- **Rotation**: Daily, kept for 30 days

### Viewing Logs

```bash
# Tail logs in real-time
tail -f logs/agentic_log_analysis.log

# View last 100 lines
tail -n 100 logs/agentic_log_analysis.log

# Search for errors
grep "ERROR" logs/agentic_log_analysis.log

# Parse JSON logs
cat logs/agentic_log_analysis.log | jq '.'
```

### Key Metrics to Monitor

1. **Execution Success Rate**: Should be >95%
2. **Log Processing Volume**: Track logs analyzed per run
3. **Agent Execution Time**: Each agent should complete within expected time
4. **Email Delivery Rate**: Should be 100%
5. **AI API Latency**: Monitor for performance degradation

### Health Check

```bash
python orchestrator/orchestrator.py --health-check
```

This validates:
- Elasticsearch connectivity
- SMTP server accessibility
- OpenAI API availability
- Configuration validity

---

## Troubleshooting

### Common Issues

#### 1. Elasticsearch Connection Failure

**Symptoms**: `ConnectionError` or `ConnectionTimeout` in logs

**Solutions**:
```bash
# Verify Elasticsearch is running
curl -u $ES_USERNAME:$ES_PASSWORD https://$ES_HOST:$ES_PORT

# Check network connectivity
ping $ES_HOST

# Verify credentials
python -c "from elasticsearch import Elasticsearch; es = Elasticsearch(['https://$ES_HOST:$ES_PORT'], basic_auth=('$ES_USERNAME', '$ES_PASSWORD')); print(es.info())"

# Check firewall rules
# Ensure port 9200 is accessible
```

#### 2. No Logs Retrieved

**Symptoms**: Analysis completes but reports 0 logs found

**Solutions**:
- Verify Filebeat is running and sending logs
- Check index pattern matches actual indices
- Verify time range includes recent data
- Check Elasticsearch query syntax

```bash
# List available indices
curl -u $ES_USERNAME:$ES_PASSWORD https://$ES_HOST:$ES_PORT/_cat/indices?v

# Verify logs exist
curl -u $ES_USERNAME:$ES_PASSWORD https://$ES_HOST:$ES_PORT/filebeat-*/_search?size=1
```

#### 3. OpenAI API Errors

**Symptoms**: `AuthenticationError` or `RateLimitError`

**Solutions**:
- Verify API key is valid
- Check API quota and billing
- Implement rate limiting
- Use exponential backoff

```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### 4. Email Delivery Failure

**Symptoms**: `SMTPAuthenticationError` or `SMTPException`

**Solutions**:
- Verify SMTP credentials
- Check "Less Secure Apps" setting (Gmail)
- Use app-specific password (Gmail)
- Verify TLS/SSL settings
- Check SMTP server logs

```bash
# Test SMTP connection
python -c "import smtplib; server = smtplib.SMTP('$SMTP_HOST', $SMTP_PORT); server.starttls(); server.login('$SMTP_USERNAME', '$SMTP_PASSWORD'); print('SMTP OK')"
```

#### 5. High Memory Usage

**Symptoms**: System slowdown, OOM errors

**Solutions**:
- Reduce `MAX_LOGS_PER_RUN` in configuration
- Increase pagination size
- Add memory limits to orchestrator
- Run during off-peak hours

#### 6. Agent Timeout

**Symptoms**: Agent execution exceeds expected time

**Solutions**:
- Check Elasticsearch query performance
- Optimize AI prompts for faster responses
- Increase timeout values in configuration
- Review agent logs for bottlenecks

### Debug Mode

Enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
python orchestrator/orchestrator.py --mode manual --hours 1
```

### Validation Commands

```bash
# Validate all configurations
python utils/helpers.py --validate-all

# Test Elasticsearch connection
python agents/log_fetcher_agent.py --test-connection

# Test AI integration
python agents/solution_gen_agent.py --test-ai

# Test email sending
python agents/email_sender_agent.py --send-test-email
```

---

## Maintenance

### Daily Tasks

- Monitor execution logs for errors
- Verify email delivery
- Check disk space for log files

### Weekly Tasks

- Review analysis quality
- Update AI prompts if needed
- Check for dependency updates
- Review error trends

### Monthly Tasks

- Rotate API keys
- Update dependencies
- Review and optimize queries
- Archive old logs
- Performance tuning

### Dependency Updates

```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade elasticsearch

# Update all packages
pip install --upgrade -r requirements.txt

# Test after updates
python orchestrator/orchestrator.py --health-check
```

### Log Rotation

Logs are automatically rotated daily. To manually clean old logs:

```bash
# Remove logs older than 30 days
find logs/ -name "*.log" -mtime +30 -delete
```

---

## Emergency Procedures

### System Down

1. Check Elasticsearch availability
2. Verify network connectivity
3. Review recent logs for errors
4. Restart orchestrator
5. Escalate if issue persists

### Critical Error Alert

1. Review email alert details
2. Check affected services
3. Verify root cause analysis
4. Execute recommended solutions
5. Monitor for resolution
6. Update runbook if new issue type

### Data Loss Prevention

- Elasticsearch maintains log retention (configure per policy)
- System logs are backed up daily
- Configuration files are version controlled
- Email alerts provide audit trail

### Rollback Procedure

If an update causes issues:

```bash
# Revert to previous version
git checkout <previous-commit>

# Reinstall dependencies
pip install -r requirements.txt

# Restart system
python orchestrator/orchestrator.py --mode scheduled
```

---

## Support Contacts

- **Elasticsearch Issues**: DevOps Team
- **AI/OpenAI Issues**: ML Engineering Team
- **Email/SMTP Issues**: IT Support
- **Application Bugs**: Development Team

---

## Appendix

### Useful Commands

```bash
# View system status
python orchestrator/orchestrator.py --status

# Generate test data
python utils/helpers.py --generate-test-logs

# Export analysis results
python orchestrator/orchestrator.py --export-results --format json

# Clear cache
python utils/helpers.py --clear-cache
```

### Configuration Templates

See `config/*.yaml.example` for configuration templates.

### API Documentation

- Elasticsearch: https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html
- OpenAI: https://platform.openai.com/docs/api-reference
- Python SMTP: https://docs.python.org/3/library/smtplib.html

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-17  
**Maintained By**: DevOps + AI Architecture Team
