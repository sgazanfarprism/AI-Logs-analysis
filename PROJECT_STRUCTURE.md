# AI Log Analysis System - Production Files

## Essential Files Structure

```
AI-Logs-analysis/
├── agents/                    # Core agent modules
│   ├── email_sender_agent.py
│   ├── error_parser_agent.py
│   ├── log_fetcher_agent.py
│   ├── rca_analyzer_agent.py
│   └── solution_gen_agent.py
│
├── orchestrator/              # Main orchestration
│   └── orchestrator.py
│
├── utils/                     # Utility functions
│   ├── exceptions.py
│   ├── helpers.py
│   └── logger.py
│
├── config/                    # Configuration files
│   ├── ai.yaml
│   ├── elasticsearch.yaml
│   └── smtp.yaml
│
├── logs/                      # Log storage
│   └── ecs_logs_*.csv        # Fetched logs
│
├── results/                   # Analysis results
│   └── ecs_analysis_*.json   # RCA and solutions
│
├── fetch_1hour_logs.py       # Main production script
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── .env.example              # Environment template
├── README.md                  # Documentation
└── GEMINI_QUICKSTART.md      # Gemini setup guide
```

## Deleted Files (Test/Development)

The following test and development files have been removed:

- ❌ `test_configuration.py` - Configuration testing
- ❌ `test_gemini.py` - Gemini API testing
- ❌ `test_smtp.py` - SMTP testing
- ❌ `test_e2e_pipeline.py` - End-to-end pipeline test
- ❌ `test_e2e_minimal.py` - Minimal E2E test
- ❌ `test_e2e_simple.py` - Simple E2E test
- ❌ `send_test_email.py` - Email testing
- ❌ `analyze_kibana_csv.py` - Kibana CSV analyzer
- ❌ `auto_download_kibana_logs.py` - Kibana automation
- ❌ `fetch_and_analyze_real_logs.py` - Old fetcher
- ❌ `fetch_ecs_logs_and_analyze.py` - Old ECS fetcher
- ❌ `list_log_groups.py` - Log group lister

## Production Files Kept

### Main Script
- ✅ **`fetch_1hour_logs.py`** - Production log fetcher and analyzer

### Core Agents
- ✅ `agents/log_fetcher_agent.py` - Fetch logs from Elasticsearch
- ✅ `agents/error_parser_agent.py` - Parse and classify errors
- ✅ `agents/rca_analyzer_agent.py` - Root cause analysis
- ✅ `agents/solution_gen_agent.py` - Generate solutions
- ✅ `agents/email_sender_agent.py` - Send email alerts

### Orchestration
- ✅ `orchestrator/orchestrator.py` - Main pipeline orchestrator

### Utilities
- ✅ `utils/helpers.py` - Helper functions
- ✅ `utils/logger.py` - Logging utilities
- ✅ `utils/exceptions.py` - Custom exceptions

### Configuration
- ✅ `config/ai.yaml` - AI/Gemini configuration
- ✅ `config/elasticsearch.yaml` - Elasticsearch settings
- ✅ `config/smtp.yaml` - Email settings

### Documentation
- ✅ `README.md` - Main documentation
- ✅ `GEMINI_QUICKSTART.md` - Gemini setup guide
- ✅ `.env.example` - Environment template

### Data
- ✅ `logs/` - Fetched log files (CSV)
- ✅ `results/` - Analysis results (JSON)

## Usage

### Fetch and Analyze Logs (Last 1 Hour)
```bash
python fetch_1hour_logs.py
```

### Run Full Orchestrator (Scheduled)
```bash
python orchestrator/orchestrator.py --mode manual --hours 1
```

### Setup Environment
1. Copy `.env.example` to `.env`
2. Add your credentials:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - GEMINI_API_KEY
   - SMTP credentials

## Next Steps

1. **Set up automated hourly runs** using Windows Task Scheduler or cron
2. **Configure email alerts** in `config/smtp.yaml`
3. **Review logs** in `logs/ecs_logs_*.csv`
4. **Check analysis results** in `results/ecs_analysis_*.json`

## Clean Project Structure

The project now contains only essential production files. All test files have been removed to keep the codebase clean and focused.
