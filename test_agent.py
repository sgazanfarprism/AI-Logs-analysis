"""
Test Agent with Existing CSV Logs - Final Version

Reads CSV logs, runs complete analysis with AI, and sends email.
"""

import os
import sys
import csv
import json
from datetime import datetime
from pathlib import Path

# CRITICAL: Load environment variables FIRST before importing agents
from dotenv import load_dotenv
load_dotenv()

print("="*80)
print("Testing AI Log Analysis Agent")
print("="*80)

# Verify Gemini API key is loaded
if not os.getenv("GEMINI_API_KEY"):
    print("\n⚠ Warning: GEMINI_API_KEY not found in environment")
    print("  Analysis will use rule-based methods only")
else:
    print(f"\n✓ Gemini API Key loaded: {os.getenv('GEMINI_API_KEY')[:20]}...")

# Find the latest CSV file
logs_dir = Path("logs")
csv_files = list(logs_dir.glob("ecs_logs_*.csv"))

if not csv_files:
    print("\n✗ No CSV files found in /logs folder")
    sys.exit(1)

# Get the most recent CSV
csv_file = max(csv_files, key=lambda p: p.stat().st_mtime)
print(f"\n[1/5] Reading CSV file...")
print(f"  File: {csv_file}")

# Read CSV
try:
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        logs = list(reader)
    
    print(f"  ✓ Loaded {len(logs):,} log entries")
except Exception as e:
    print(f"  ✗ Error reading CSV: {e}")
    sys.exit(1)

# Normalize logs
print("\n[2/5] Normalizing logs...")

normalized_logs = []
error_count = 0
warning_count = 0

for log in logs:
    message = log.get('message', '')
    message_lower = message.lower()
    
    if any(kw in message_lower for kw in ['error', 'exception', 'failed', 'failure']):
        log_level = "error"
        error_count += 1
    elif 'warn' in message_lower:
        log_level = "warning"
        warning_count += 1
    elif any(kw in message_lower for kw in ['fatal', 'critical']):
        log_level = "critical"
        error_count += 1
    else:
        log_level = "info"
    
    normalized_logs.append({
        "timestamp": log.get('timestamp', ''),
        "message": message,
        "log_level": log_level,
        "service_name": log.get('service', 'CA-PROD-API-SERVICE'),
        "host_name": log.get('logStreamName', 'unknown'),
        "error_message": message if log_level in ["error", "critical"] else "",
        "error_stack_trace": "",
        "error_type": "",
        "event_dataset": f"ecs.{log.get('cluster', 'CA-PROD-CLR')}",
        "event_module": "ecs",
        "raw": {}
    })

print(f"  ✓ Normalized {len(normalized_logs):,} logs")
print(f"  ✓ Errors: {error_count:,} | Warnings: {warning_count:,}")

# Run analysis
print("\n[3/5] Running analysis...")

try:
    from agents.error_parser_agent import ErrorParserAgent
    from agents.rca_analyzer_agent import RCAAnalyzerAgent
    from agents.solution_gen_agent import SolutionGeneratorAgent
    
    # Parse
    print("  → Parsing errors...")
    parser = ErrorParserAgent()
    parse_result = parser.parse_logs(normalized_logs)
    print(f"    ✓ {len(parse_result['error_groups'])} error groups")
    
    if len(parse_result['error_groups']) > 0:
        # RCA
        print("  → RCA analysis...")
        analyzer = RCAAnalyzerAgent()
        rca_result = analyzer.analyze(
            parse_result["error_groups"],
            parse_result["patterns"],
            parse_result["statistics"]
        )
        print(f"    ✓ {len(rca_result['root_causes'])} root causes")
        
        # Solutions
        print("  → Generating solutions...")
        generator = SolutionGeneratorAgent()
        solutions = generator.generate_solutions(
            rca_result,
            parse_result["error_groups"],
            parse_result["statistics"]
        )
        print(f"    ✓ {len(solutions['solutions'])} solutions")
    else:
        print("  ✓ No errors - system healthy!")
        rca_result = {"root_causes": [], "confidence_score": 100}
        solutions = {"solutions": [], "overall_confidence": 100}

except Exception as e:
    print(f"  ✗ Analysis failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Save
print("\n[4/5] Saving results...")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

result_file = results_dir / f"test_analysis_{timestamp}.json"

with open(result_file, 'w') as f:
    json.dump({
        "source": "csv_test",
        "csv_file": str(csv_file),
        "logs_analyzed": len(normalized_logs),
        "errors_found": error_count,
        "warnings_found": warning_count,
        "parse_result": parse_result,
        "rca_result": rca_result,
        "solutions": solutions
    }, f, indent=2, default=str)

print(f"  ✓ Saved: {result_file}")

# Email
print("\n[5/5] Sending email...")

email_sent = False
try:
    from agents.email_sender_agent import EmailSenderAgent
    
    sender = EmailSenderAgent()
    execution_result = {
        "execution_id": timestamp,
        "start_time": datetime.utcnow().isoformat() + "Z"
    }
    
    if error_count == 0:
        time_range = f"✅ All Clear - No Errors ({len(normalized_logs):,} logs)"
    else:
        time_range = f"⚠️ {error_count:,} errors in {len(normalized_logs):,} logs"
    
    email_sent = sender.send_alert(
        execution_result,
        parse_result["error_groups"],
        rca_result,
        solutions,
        parse_result["statistics"],
        time_range
    )
    
    print(f"  {'✓ Sent!' if email_sent else '⚠ Failed/Skipped'}")

except Exception as e:
    print(f"  ✗ Error: {e}")

# Summary
print("\n" + "="*80)
print("✓ TEST COMPLETED!")
print("="*80)
print(f"\nResults:")
print(f"  • Logs: {len(normalized_logs):,}")
print(f"  • Errors: {error_count:,}")
print(f"  • Warnings: {warning_count:,}")
print(f"  • Error Groups: {len(parse_result['error_groups'])}")

if error_count > 0:
    print(f"  • Root Causes: {len(rca_result['root_causes'])}")
    print(f"  • Solutions: {len(solutions['solutions'])}")
    
    if parse_result['error_groups']:
        print(f"\n  Top Errors:")
        for i, group in enumerate(parse_result['error_groups'][:3], 1):
            print(f"    {i}. {group['error_type']} ({group['count']}x)")
else:
    print(f"\n  ✅ No errors - system healthy!")

print(f"\n  Email: {'✓ Sent' if email_sent else '⚠ Failed'}")
print(f"  Results: {result_file}")
print("\n" + "="*80)
