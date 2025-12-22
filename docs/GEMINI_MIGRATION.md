# Migration to Google Gemini API

## Overview

The Agentic AI Log Analysis System has been migrated from OpenAI to **Google Gemini API** for AI-powered analysis.

## Changes Made

### 1. Dependencies Updated
**File**: `requirements.txt`
- **Removed**: `openai>=1.6.0`
- **Added**: `google-generativeai>=0.3.0`

### 2. Configuration Updated
**File**: `config/ai.yaml`
- Provider changed from `openai` to `gemini`
- API key variable changed from `${OPENAI_API_KEY}` to `${GEMINI_API_KEY}`
- Model changed to `${GEMINI_MODEL}` (supports: gemini-pro, gemini-1.5-pro, gemini-1.5-flash)
- Removed OpenAI-specific parameters: `frequency_penalty`, `presence_penalty`
- Added Gemini-specific parameter: `top_k: 40`

### 3. Environment Variables Updated
**File**: `.env`
```bash
# OLD (OpenAI)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# NEW (Gemini)
GEMINI_API_KEY=AIzaSyAryOZ5TmjfIuqeSXI0IdI4WwGwrTzDkXk
GEMINI_MODEL=gemini-pro
```

### 4. Agent Code Updated

#### RCA Analyzer Agent (`agents/rca_analyzer_agent.py`)
- Updated `_initialize_ai_client()` to use `google.generativeai`
- Updated `_ai_powered_rca()` to use Gemini's `GenerativeModel` API
- Changed from OpenAI's chat completion to Gemini's content generation

#### Solution Generator Agent (`agents/solution_gen_agent.py`)
- Updated `_initialize_ai_client()` to use `google.generativeai`
- Updated `_ai_generate_solution()` to use Gemini's `GenerativeModel` API
- Changed from OpenAI's chat completion to Gemini's content generation

## API Differences

### OpenAI API (Old)
```python
import openai
openai.api_key = api_key
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.3,
    max_tokens=2000
)
result = response.choices[0].message.content
```

### Gemini API (New)
```python
import google.generativeai as genai
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-pro")
response = model.generate_content(
    full_prompt,
    generation_config={
        "temperature": 0.3,
        "max_output_tokens": 2000,
        "top_p": 1.0,
        "top_k": 40
    }
)
result = response.text
```

## Available Gemini Models

- **gemini-pro**: Standard model for text generation
- **gemini-1.5-pro**: Enhanced model with larger context window
- **gemini-1.5-flash**: Faster, optimized for quick responses

## Testing

After installation, test the Gemini integration:

```bash
# Install dependencies
pip install google-generativeai

# Test RCA Analyzer
python agents/rca_analyzer_agent.py --test

# Test Solution Generator
python agents/solution_gen_agent.py --test

# Run full analysis
python orchestrator/orchestrator.py --mode manual --hours 1
```

## Benefits of Gemini

1. **Cost-effective**: Generally lower cost than GPT-4
2. **Fast**: Quick response times
3. **Large context**: Gemini 1.5 Pro supports up to 1M tokens
4. **Free tier**: Available for testing and development

## Fallback Behavior

If Gemini API fails or is unavailable, the system automatically falls back to **rule-based analysis** for:
- Root Cause Analysis (RCA Analyzer)
- Solution Generation (Solution Generator)

This ensures the system continues to function even without AI.

## API Key Security

Your Gemini API key is stored in:
- `.env` file (gitignored, not committed to version control)
- Loaded at runtime via environment variables
- Never hardcoded in source code

## Next Steps

1. ✅ Dependencies updated
2. ✅ Configuration updated
3. ✅ Agent code updated
4. ✅ Environment variables set
5. ⏳ Install google-generativeai package
6. ⏳ Test Gemini integration
7. ⏳ Run end-to-end analysis

---

**Migration Date**: 2025-12-20  
**Status**: Complete - Ready for Testing
