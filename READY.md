# ✅ System Ready - Quick Reference

## 🎉 All Tests Passed!

```
✅ PASS - CSV Export
✅ PASS - Error Detection  
✅ PASS - Signature Generation
✅ PASS - Conditional Workflow

Total: 4/4 tests passed
```

---

## 🚀 Run Commands (Use These!)

### Activate Virtual Environment First
```powershell
.venv\Scripts\Activate.ps1
```

### Run Analysis Commands

**1. Analyze Last Hour**
```powershell
python run_analysis.py --mode manual --hours 1
```

**2. Analyze Last 24 Hours**
```powershell
python run_analysis.py --mode manual --hours 24
```

**3. Test Without Email**
```powershell
python run_analysis.py --mode manual --hours 1 --no-email
```

**4. Health Check**
```powershell
python run_analysis.py --health-check
```

**5. Specific Time Range**
```powershell
python run_analysis.py --mode manual --start "2025-12-30T20:00:00" --end "2025-12-30T22:00:00"
```

---

## ⚙️ Before First Run

### 1. Configure Elasticsearch
Edit `config/elasticsearch.yaml`:
```yaml
host: your-elasticsearch-host
port: 9200
username: elastic
password: your-password
index_pattern: filebeat-*
```

### 2. Configure Email (Optional for testing)
Edit `config/smtp.yaml`:
```yaml
host: smtp.gmail.com
port: 587
username: your-email@gmail.com
password: your-app-password
recipients: team@company.com
```

### 3. Verify .env File
Check `.env` has:
```bash
GEMINI_API_KEY=AIzaSyAryOZ5TmjfIuqeSXI0IdI4WwGwrTzDkXk
GEMINI_MODEL=gemini-pro
```

---

## 📊 What Happens

### No Errors Found ✅
```
Status: completed_no_errors
Message: "No error-level logs found"
```
- No CSV generated
- No email sent

### Errors Found ⚠️
```
Status: completed_with_errors
CSV: results/errors_20251230_230500.csv
Email: Sent with CSV attachment
```

### All Duplicates 🔄
```
Status: completed_all_duplicates
Message: "All errors were duplicates"
```
- No duplicate alerts

---

## 🔧 Troubleshooting

### Module Not Found Error?
Always run from project root:
```powershell
# ✅ Correct
python run_analysis.py --mode manual --hours 1

# ❌ Wrong
python orchestrator/orchestrator.py --mode manual --hours 1
```

### Elasticsearch Connection Failed?
1. Check `config/elasticsearch.yaml` has correct host/credentials
2. Test connection:
```powershell
python -c "from agents.log_fetcher_agent import LogFetcherAgent; agent = LogFetcherAgent(); print('Connected!' if agent.test_connection() else 'Failed')"
```

### Email Not Sending?
Use `--no-email` flag for testing:
```powershell
python run_analysis.py --mode manual --hours 1 --no-email
```

---

## 📁 Output Files

**CSV Files:** `results/errors_YYYYMMDD_HHMMSS.csv`
- Only created when errors are found
- Contains all error details with ECS metadata

**Analysis Results:** `results/analysis_YYYYMMDD_HHMMSS.json`
- Complete analysis with RCA and solutions

**Logs:** `logs/agentic_log_analysis.log`
- Structured JSON logs

---

## 🎯 Next Steps

1. **Configure Elasticsearch** in `config/elasticsearch.yaml`
2. **Run first test** (without email):
   ```powershell
   python run_analysis.py --mode manual --hours 1 --no-email
   ```
3. **Check results** in `results/` directory
4. **Configure email** when ready for alerts

---

**Need Help?** See [RUN_COMMANDS.md](RUN_COMMANDS.md) for complete reference.
