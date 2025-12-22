# Agentic AI Log Analysis System v1.0

## Overview

A production-grade, fully autonomous AI-driven log analysis platform that ingests ECS-formatted logs from Filebeat, performs intelligent analysis, and generates actionable remediation solutions.

## Architecture

This system implements a multi-agent architecture where specialized AI agents collaborate to:

1. **Fetch logs** from Elasticsearch (ECS format via Filebeat)
2. **Parse and classify** errors and anomalies
3. **Perform Root Cause Analysis** (RCA) using AI reasoning
4. **Generate remediation solutions** with confidence scoring
5. **Send structured alerts** via email with complete analysis

## Key Features

- **Autonomous Operation**: Daily scheduled analysis + on-demand triggers
- **AI-Powered Intelligence**: Advanced reasoning for RCA and solution generation
- **Production-Ready**: Comprehensive error handling, structured logging, retry mechanisms
- **Modular Design**: Independent agents with clear responsibilities
- **ECS Compliance**: Native support for Elastic Common Schema via Filebeat
- **Configurable**: Environment-based configuration for all components

## System Components

### Agents
- **Log Fetcher Agent**: Queries Elasticsearch with filtering, pagination, and error handling
- **Error Parser Agent**: Classifies logs, detects patterns, groups related errors
- **RCA Analyzer Agent**: Performs causal reasoning and correlation analysis
- **Solution Generator Agent**: AI-powered remediation with preventive actions
- **Email Sender Agent**: Structured alerting with retry logic

### Orchestrator
Central coordinator managing agent execution, scheduling, and failure recovery

## Technology Stack

- **Language**: Python 3.11+
- **Log Storage**: Elasticsearch (official Python client)
- **Log Ingestion**: Filebeat (ECS format)
- **AI Provider**: OpenAI (pluggable architecture)
- **Email**: SMTP (Gmail/Office365/Custom)
- **Configuration**: YAML + Environment Variables
- **Logging**: Structured JSON

## Directory Structure

```
/agentic-log-analysis/
├── agents/                     # Specialized AI agents
│   ├── log_fetcher_agent.py
│   ├── error_parser_agent.py
│   ├── rca_analyzer_agent.py
│   ├── solution_gen_agent.py
│   └── email_sender_agent.py
├── orchestrator/               # Central coordination
│   └── orchestrator.py
├── config/                     # Configuration files
│   ├── elasticsearch.yaml
│   ├── ai.yaml
│   └── smtp.yaml
├── utils/                      # Shared utilities
│   ├── logger.py
│   ├── exceptions.py
│   └── helpers.py
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md
│   ├── DAILY_PROGRESS.md
│   └── RUNBOOK.md
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Elasticsearch cluster (accessible)
- Filebeat configured to send ECS logs to Elasticsearch
- OpenAI API key (or compatible AI provider)
- SMTP server credentials

### Installation

```bash
# Clone the repository
cd AI-Logs-analysis

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Configuration

1. **Elasticsearch** (`config/elasticsearch.yaml`): Connection details, indices, query parameters
2. **AI Provider** (`config/ai.yaml`): API keys, model selection, parameters
3. **SMTP** (`config/smtp.yaml`): Email server, credentials, recipients

### Running

```bash
# Daily scheduled analysis (runs automatically)
python orchestrator/orchestrator.py --mode scheduled

# Manual on-demand analysis
python orchestrator/orchestrator.py --mode manual --hours 24

# Specific time range
python orchestrator/orchestrator.py --mode manual --start "2025-12-17T00:00:00" --end "2025-12-17T23:59:59"
```

## Environment Variables

```bash
# Elasticsearch
ES_HOST=localhost
ES_PORT=9200
ES_USERNAME=elastic
ES_PASSWORD=changeme
ES_INDEX_PATTERN=filebeat-*

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_RECIPIENTS=team@company.com,oncall@company.com
```

## Output

Each analysis run produces:

1. **Structured Logs**: JSON-formatted execution logs
2. **Email Alerts**: Comprehensive reports with:
   - Error summary and timestamps
   - Impacted services
   - Root cause analysis
   - Recommended solutions with confidence scores
3. **Persistent State**: Progress tracking for resumable operations

## Error Handling

- Automatic retries with exponential backoff
- Graceful degradation on partial failures
- Comprehensive exception logging
- Alert on critical failures

## Monitoring

- Structured JSON logs for easy parsing
- Execution metrics and timing
- Success/failure tracking
- Agent-level performance monitoring

## Security

- Credentials via environment variables only
- No hardcoded secrets
- Secure SMTP with TLS
- API key rotation support

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md): Detailed system design
- [RUNBOOK.md](docs/RUNBOOK.md): Operational procedures
- [DAILY_PROGRESS.md](docs/DAILY_PROGRESS.md): Development tracking

## Support

For issues, enhancements, or questions, refer to the documentation or contact the DevOps team.

## License

Internal Use Only - Proprietary
