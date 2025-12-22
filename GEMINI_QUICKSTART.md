# Gemini API Integration - Quick Start Guide

## ✅ Migration Complete

Your Agentic AI Log Analysis System has been successfully migrated to **Google Gemini API**.

## 🔑 Your Gemini API Key

```
AIzaSyAryOZ5TmjfIuqeSXI0IdI4WwGwrTzDkXk
```

This key is already configured in your `.env` file.

## 📦 Installation

The system has been updated to use Gemini. Complete the installation:

```bash
# Install Gemini SDK
pip install google-generativeai

# Verify installation
pip show google-generativeai
```

## 🧪 Testing

### 1. Test Gemini Connection
```bash
python test_gemini.py
```

This will verify:
- API key is valid
- Gemini client initializes correctly
- Content generation works
- JSON response parsing works

### 2. Test Individual Agents
```bash
# Test RCA Analyzer with Gemini
python agents/rca_analyzer_agent.py --test

# Test Solution Generator with Gemini
python agents/solution_gen_agent.py --test
```

### 3. Run Full Analysis
```bash
# Manual analysis (last 1 hour)
python orchestrator/orchestrator.py --mode manual --hours 1
```

## 📝 What Changed

### Files Modified

1. **requirements.txt**
   - Removed: `openai>=1.6.0`
   - Added: `google-generativeai>=0.3.0`

2. **config/ai.yaml**
   - Provider: `openai` → `gemini`
   - API Key: `OPENAI_API_KEY` → `GEMINI_API_KEY`
   - Model: `gpt-4` → `gemini-pro`

3. **.env**
   - `GEMINI_API_KEY=AIzaSyAryOZ5TmjfIuqeSXI0IdI4WwGwrTzDkXk`
   - `GEMINI_MODEL=gemini-pro`

4. **agents/rca_analyzer_agent.py**
   - Updated to use `google.generativeai`
   - Changed API calls to Gemini format

5. **agents/solution_gen_agent.py**
   - Updated to use `google.generativeai`
   - Changed API calls to Gemini format

## 🎯 Gemini Models Available

You can change the model in `.env`:

```bash
# Fast and efficient (default)
GEMINI_MODEL=gemini-pro

# Enhanced with larger context
GEMINI_MODEL=gemini-1.5-pro

# Fastest for quick responses
GEMINI_MODEL=gemini-1.5-flash
```

## 🔄 How It Works

### Before (OpenAI)
```python
import openai
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[...]
)
```

### After (Gemini)
```python
import google.generativeai as genai
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-pro")
response = model.generate_content(prompt)
```

## 🛡️ Fallback Behavior

If Gemini API fails, the system automatically uses **rule-based analysis**:
- RCA Analyzer: Pattern-based root cause detection
- Solution Generator: Pre-defined solution templates

Your system will **never fail completely** - it gracefully degrades to rule-based mode.

## 💰 Cost Benefits

Gemini offers:
- **Lower cost** than GPT-4
- **Free tier** for testing
- **Fast responses**
- **Large context window** (1M tokens for 1.5 Pro)

## 🔐 Security

Your API key is:
- ✅ Stored in `.env` (gitignored)
- ✅ Loaded via environment variables
- ✅ Never hardcoded in source
- ✅ Not committed to version control

## 📊 Next Steps

1. **Install Package** (if not done):
   ```bash
   pip install google-generativeai
   ```

2. **Test Connection**:
   ```bash
   python test_gemini.py
   ```

3. **Run Analysis**:
   ```bash
   python orchestrator/orchestrator.py --mode manual --hours 1
   ```

4. **Check Results**:
   - Logs: `logs/agentic_log_analysis.log`
   - Results: `results/analysis_*.json`
   - Email: Check your inbox for alerts

## 🆘 Troubleshooting

### Error: "API key not valid"
- Verify key at: https://makersuite.google.com/app/apikey
- Check `.env` file has correct key
- Ensure no extra spaces in the key

### Error: "Module not found: google.generativeai"
```bash
pip install google-generativeai
```

### Error: "Rate limit exceeded"
- Gemini free tier has limits
- Wait a few minutes and retry
- Consider upgrading to paid tier

## 📚 Documentation

- [Gemini Migration Guide](docs/GEMINI_MIGRATION.md)
- [Flow Diagrams](docs/FLOW_DIAGRAMS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Runbook](docs/RUNBOOK.md)

---

**Status**: ✅ Ready to Test  
**API Provider**: Google Gemini  
**Model**: gemini-pro  
**Date**: 2025-12-20
