# Quick Start Guide - Enhanced Error Detection System

## ✅ System Status: Ready for Production

All tests passed! The enhanced error detection system is fully operational.

---

## 🚀 Quick Test (30 seconds)

Run the comprehensive test suite:
```bash
python test_enhanced_system.py
```

**Expected Output:**
```
✅ PASS - CSV Export
✅ PASS - Error Detection
✅ PASS - Signature Generation
✅ PASS - Conditional Workflow

Total: 4/4 tests passed
🎉 All tests passed! System is ready for production use.
```

---

## 📋 Most Common Commands

### 1. Analyze Last Hour (Most Common)
```bash
python orchestrator/orchestrator.py --mode manual --hours 1
```

### 2. Analyze Last 24 Hours
```bash
python orchestrator/orchestrator.py --mode manual --hours 24
```

### 3. Test Without Sending Email
```bash
python orchestrator/orchestrator.py --mode manual --hours 1 --no-email
```

### 4. Health Check
```bash
python orchestrator/orchestrator.py --health-check
```

---

## 📊 What Happens When You Run?

### Scenario A: No Errors Found ✅
```
Status: completed_no_errors
Message: "Analysis completed successfully - no error-level logs found"
```
- ✅ No CSV file generated
- ✅ No email sent
- ✅ Fast execution

### Scenario B: Errors Found ⚠️
```
Status: completed_with_errors
CSV File: results/errors_20251230_225400.csv
Email: Sent with CSV attachment
```
- ✅ CSV file with all error details
- ✅ Email alert with RCA and solutions
- ✅ CSV attached to email

### Scenario C: All Duplicates 🔄
```
Status: completed_all_duplicates
Message: "All detected errors were duplicates from previous analysis"
```
- ✅ No duplicate alerts
- ✅ Deduplication working correctly

---

## 📁 Output Files

### CSV Files (Only When Errors Found)
**Location:** `results/errors_YYYYMMDD_HHMMSS.csv`

**Columns:**
- Timestamp
- ECS Cluster Name
- ECS Service / Task Name
- Log Level
- Error Message
- Stack Trace
- Container Name
- Environment

**Example:**
```csv
Timestamp,ECS Cluster Name,ECS Service / Task Name,Log Level,Error Message,Stack Trace,Container Name,Environment
2025-12-30 22:00:00 UTC,prod-ecs-cluster,user-service,ERROR,NullPointerException in UserController,at com.example.UserController.getUser(UserController.java:45),user-service-container,production
```

### Analysis Results
**Location:** `results/analysis_YYYYMMDD_HHMMSS.json`

Contains complete analysis with RCA and solutions.

### Logs
**Location:** `logs/agentic_log_analysis.log`

JSON-formatted structured logs.

---

## 🔧 Configuration

### Required Environment Variables (`.env`)

```bash
# Elasticsearch
ES_HOST=your-elasticsearch-host
ES_PORT=9200
ES_USERNAME=elastic
ES_PASSWORD=your-password
ES_INDEX_PATTERN=filebeat-*

# Gemini API
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-pro

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_RECIPIENTS=team@company.com,oncall@company.com
```

---

## 🎯 Key Features

### 1. Intelligent Error Detection
- ✅ Only processes logs with ERROR/EXCEPTION/FAILURE/CRITICAL
- ✅ Skips RCA and alerts when no errors found
- ✅ Saves time and reduces noise

### 2. CSV Export
- ✅ Comprehensive ECS metadata
- ✅ Timestamped filenames
- ✅ CSV injection prevention
- ✅ Handles missing fields gracefully

### 3. Error Deduplication
- ✅ Generates unique signatures for errors
- ✅ Prevents duplicate alerts
- ✅ Normalizes variable parts (timestamps, IDs, line numbers)

### 4. Email Attachments
- ✅ CSV files attached to alert emails
- ✅ Complete error details for offline analysis
- ✅ MIME multipart support

---

## 📖 Full Documentation

- **[RUN_COMMANDS.md](file:///c:/Users/sgazanfar/AI-Logs-analysis/RUN_COMMANDS.md)** - Complete command reference
- **[walkthrough.md](file:///C:/Users/sgazanfar/.gemini/antigravity/brain/9f0f80b7-efc7-4760-8dc1-31c572fe34d3/walkthrough.md)** - Implementation details and test results
- **[implementation_plan.md](file:///C:/Users/sgazanfar/.gemini/antigravity/brain/9f0f80b7-efc7-4760-8dc1-31c572fe34d3/implementation_plan.md)** - Technical design

---

## 🆘 Troubleshooting

### Test Failed?
```bash
# Check Python version (need 3.11+)
python --version

# Verify dependencies
pip install -r requirements.txt

# Test individual components
python -m utils.csv_exporter --test
python agents/error_parser_agent.py --test
```

### Elasticsearch Connection Issues?
```bash
# Test connection
python -c "from agents.log_fetcher_agent import LogFetcherAgent; agent = LogFetcherAgent(); print('✅ Connected' if agent.test_connection() else '❌ Failed')"

# Check config
python -c "from utils.helpers import load_yaml_config; print(load_yaml_config('config/elasticsearch.yaml'))"
```

### Email Not Sending?
```bash
# Send test email
python agents/email_sender_agent.py --send-test-email

# Check SMTP config
python -c "from utils.helpers import load_yaml_config; print(load_yaml_config('config/smtp.yaml'))"
```

---

## 🎉 You're Ready!

Run your first analysis:
```bash
python orchestrator/orchestrator.py --mode manual --hours 1
```

Check the results:
```bash
# View latest CSV
Get-ChildItem results/errors_*.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# View logs
Get-Content logs/agentic_log_analysis.log -Tail 20
```

---

**Need Help?** See [RUN_COMMANDS.md](file:///c:/Users/sgazanfar/AI-Logs-analysis/RUN_COMMANDS.md) for complete command reference.
