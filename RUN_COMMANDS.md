# Run Commands for Enhanced Error Detection System

## Quick Start

### 1. Run Comprehensive Test Suite
```bash
python test_enhanced_system.py
```
**What it tests:**
- CSV export functionality
- Error detection logic
- Error signature generation
- Conditional workflow

---

## Production Usage

### Manual Analysis (Last 1 Hour)
```bash
python orchestrator/orchestrator.py --mode manual --hours 1
```

### Manual Analysis (Last 24 Hours)
```bash
python orchestrator/orchestrator.py --mode manual --hours 24
```

### Manual Analysis (Specific Time Range)
```bash
python orchestrator/orchestrator.py --mode manual --start "2025-12-30T20:00:00" --end "2025-12-30T22:00:00"
```

### Manual Analysis (No Email - Testing)
```bash
python orchestrator/orchestrator.py --mode manual --hours 1 --no-email
```

### Filter by Service
```bash
python orchestrator/orchestrator.py --mode manual --hours 1 --service "user-service,payment-service"
```

### Filter by Severity
```bash
python orchestrator/orchestrator.py --mode manual --hours 1 --severity "error,critical"
```

---

## Scheduled Mode

### Daily Analysis at 2:00 AM (Default)
```bash
python orchestrator/orchestrator.py --mode scheduled
```

### Daily Analysis at Custom Time
```bash
python orchestrator/orchestrator.py --mode scheduled --schedule-time "03:00" --hours 24
```

---

## Health Checks

### System Health Check
```bash
python orchestrator/orchestrator.py --health-check
```
**Checks:**
- Elasticsearch connectivity
- Email configuration
- AI (Gemini) client status

### System Status
```bash
python orchestrator/orchestrator.py --status
```

---

## Individual Component Tests

### Test CSV Exporter
```bash
python -m utils.csv_exporter --test
```

### Test Error Parser Agent
```bash
python agents/error_parser_agent.py --test
```

### Test Email Sender (Send Test Email)
```bash
python agents/email_sender_agent.py --send-test-email
```

### Test RCA Analyzer
```bash
python agents/rca_analyzer_agent.py --test
```

### Test Solution Generator
```bash
python agents/solution_gen_agent.py --test
```

---

## Expected Outputs

### Scenario 1: No Errors Found
```json
{
  "status": "completed_no_errors",
  "message": "Analysis completed successfully - no error-level logs found"
}
```
**Result:** No CSV, no email

### Scenario 2: Errors Found
```json
{
  "status": "completed_with_errors",
  "csv_file": "results/errors_20251230_225400.csv",
  "stages": {
    "error_parsing": {"status": "success", "error_groups": 5},
    "rca_analysis": {"status": "success", "root_causes": 2},
    "solution_generation": {"status": "success", "solutions": 2},
    "email_sending": {"status": "success"}
  }
}
```
**Result:** CSV generated, email sent with attachment

### Scenario 3: All Duplicates
```json
{
  "status": "completed_all_duplicates",
  "message": "All detected errors were duplicates from previous analysis",
  "deduplication": {
    "original_count": 5,
    "duplicate_count": 5,
    "unique_count": 0
  }
}
```
**Result:** No duplicate alerts

---

## Monitoring Commands

### View Recent Logs
```bash
Get-Content logs/agentic_log_analysis.log -Tail 50
```

### Check for Deduplication Events
```bash
Select-String -Path logs/agentic_log_analysis.log -Pattern "Skipping duplicate error"
```

### List Generated CSV Files
```bash
Get-ChildItem results/errors_*.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 10
```

### View Latest CSV File
```bash
$latestCsv = Get-ChildItem results/errors_*.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $latestCsv.FullName | Select-Object -First 20
```

---

## Troubleshooting

### Check Python Version
```bash
python --version
```
**Required:** Python 3.11+

### Verify Dependencies
```bash
pip list | Select-String -Pattern "google-generativeai|elasticsearch|pyyaml"
```

### Test Elasticsearch Connection
```bash
python -c "from agents.log_fetcher_agent import LogFetcherAgent; agent = LogFetcherAgent(); print('✅ Connected' if agent.test_connection() else '❌ Failed')"
```

### Test Gemini API
```bash
python -c "import google.generativeai as genai; import os; genai.configure(api_key=os.getenv('GEMINI_API_KEY')); model = genai.GenerativeModel('gemini-pro'); response = model.generate_content('Test'); print('✅ Gemini API working')"
```

### Validate Configuration Files
```bash
python -c "from utils.helpers import load_yaml_config; print('ES:', load_yaml_config('config/elasticsearch.yaml').get('host')); print('SMTP:', load_yaml_config('config/smtp.yaml').get('host'))"
```

---

## Development Commands

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Activate Virtual Environment
```bash
.venv\Scripts\Activate.ps1
```

### Run Linter (if installed)
```bash
flake8 agents/ orchestrator/ utils/
```

### Format Code (if black installed)
```bash
black agents/ orchestrator/ utils/
```

---

## Workflow Examples

### Morning Check (Last Night's Logs)
```bash
# Analyze logs from midnight to now
python orchestrator/orchestrator.py --mode manual --hours 8
```

### Incident Investigation
```bash
# Analyze specific incident time window
python orchestrator/orchestrator.py --mode manual --start "2025-12-30T14:30:00" --end "2025-12-30T15:00:00" --no-email
```

### Weekly Summary
```bash
# Analyze last 7 days
python orchestrator/orchestrator.py --mode manual --hours 168
```

---

## Output Files

### CSV Files
Location: `results/errors_YYYYMMDD_HHMMSS.csv`

Columns:
- Timestamp
- ECS Cluster Name
- ECS Service / Task Name
- Log Level
- Error Message
- Stack Trace
- Container Name
- Environment

### Analysis Results
Location: `results/analysis_YYYYMMDD_HHMMSS.json`

Contains:
- Complete analysis metadata
- Error groups
- RCA results
- Generated solutions

### Logs
Location: `logs/agentic_log_analysis.log`

Format: JSON structured logging

---

## Environment Variables

Required in `.env`:
```bash
# Elasticsearch
ES_HOST=your-elasticsearch-host
ES_PORT=9200
ES_USERNAME=elastic
ES_PASSWORD=your-password

# Gemini API
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-pro

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_RECIPIENTS=team@company.com
```

---

## Performance Tips

1. **Limit Time Range:** Use `--hours` to limit log volume
2. **Filter by Service:** Use `--service` to focus on specific services
3. **Skip Email for Testing:** Use `--no-email` during development
4. **Monitor Deduplication:** Check logs to see how many duplicates are filtered

---

## Support

For issues or questions:
1. Check `logs/agentic_log_analysis.log` for detailed error messages
2. Run `--health-check` to verify all components
3. Test individual agents to isolate issues
4. Review `docs/RUNBOOK.md` for operational procedures
