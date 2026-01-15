---
description: Initialize the AI Log Analysis System environment
---

# Project Initialization Workflow

This workflow sets up the AI Log Analysis System environment and verifies all dependencies.

## Steps

// turbo-all

1. **Verify Python Version**
```bash
python --version
```
Ensure Python 3.11+ is installed.

2. **Create Virtual Environment** (if not exists)
```bash
python -m venv .venv
```

3. **Activate Virtual Environment**
```bash
.venv\Scripts\Activate.ps1
```

4. **Install Dependencies**
```bash
pip install -r requirements.txt
```

5. **Verify Gemini SDK Installation**
```bash
pip show google-generativeai
```

6. **Check Environment Configuration**
```bash
if (Test-Path .env) { Write-Host "✅ .env file exists" } else { Write-Host "⚠️  .env file missing - copy from .env.example"; Copy-Item .env.example .env }
```

7. **Verify Required Directories**
```bash
$dirs = @("logs", "results", "config", "agents", "orchestrator", "utils", "docs")
foreach ($dir in $dirs) { if (Test-Path $dir) { Write-Host "✅ $dir exists" } else { Write-Host "⚠️  $dir missing"; New-Item -ItemType Directory -Path $dir } }
```

8. **Test Gemini Connection** (if test_gemini.py exists)
```bash
if (Test-Path test_gemini.py) { python test_gemini.py } else { Write-Host "⚠️  test_gemini.py not found - skipping connection test" }
```

9. **Display System Status**
```bash
Write-Host "`n=== AI Log Analysis System - Initialization Complete ===`n"
Write-Host "📦 Dependencies: Installed"
Write-Host "🔑 API Provider: Google Gemini"
Write-Host "📁 Project Structure: Verified"
Write-Host "`nNext Steps:"
Write-Host "1. Configure .env with your credentials"
Write-Host "2. Update config/elasticsearch.yaml with your ES cluster details"
Write-Host "3. Update config/smtp.yaml with your email settings"
Write-Host "4. Run: python orchestrator/orchestrator.py --mode manual --hours 1"
```

## Post-Initialization Checklist

- [ ] `.env` file configured with valid credentials
- [ ] Elasticsearch connection details updated
- [ ] SMTP settings configured
- [ ] Gemini API key verified
- [ ] Test run completed successfully
