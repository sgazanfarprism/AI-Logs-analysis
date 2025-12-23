"""
Download Logs from Kibana via Browser and Analyze

This script uses browser automation to download logs as CSV from Kibana,
then runs the analysis pipeline.
"""

import sys
import os
import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("="*80)
print("Kibana Log Download and Analysis")
print("="*80)
print("\nIMPORTANT: This script will guide you through downloading logs from Kibana.")
print("Please follow these steps:\n")
print("1. Open your browser and go to: https://logs.prismxai.com/")
print("2. Login with:")
print("   Username: prism-user")
print("   Password: PrismView2025!")
print("3. Navigate to 'Discover' (Analytics > Discover)")
print("4. Select the time range (e.g., Last 30 days)")
print("5. Select the index pattern (e.g., CA-PROD-ECS-LOGS)")
print("6. Click 'Share' > 'CSV Reports' > 'Generate CSV'")
print(f"7. Save the CSV file to: {Path('logs').absolute()}")
print("8. Name it: kibana_logs.csv")
print("\n" + "="*80)

# Wait for user to download
input("\nPress ENTER after you have downloaded the CSV file to logs/kibana_logs.csv...")

# Check if file exists
csv_file = Path("logs/kibana_logs.csv")
if not csv_file.exists():
    print(f"\n✗ File not found: {csv_file}")
    print("Please download the CSV and try again.")
    sys.exit(1)

print(f"\n✓ Found CSV file: {csv_file}")

# Read and process CSV
print("\n[1/4] Reading CSV file...")
try:
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        logs = list(reader)
    
    print(f"  ✓ Loaded {len(logs)} log entries")
    
    if logs:
        print(f"  ✓ Fields: {len(logs[0].keys())}")
        print(f"  Sample fields: {list(logs[0].keys())[:5]}")
        
except Exception as e:
    print(f"  ✗ Failed to read CSV: {str(e)}")
    sys.exit(1)

# Normalize logs for analysis
print("\n[2/4] Normalizing logs for analysis...")

normalized_logs = []
for log in logs:
    # Map CSV fields to our expected format
    normalized = {
        "timestamp": log.get("@timestamp") or log.get("timestamp", datetime.utcnow().isoformat()),
        "message": log.get("message", ""),
        "log_level": (
            log.get("log.level") or 
            log.get("level") or 
            log.get("severity") or 
            "info"
        ),
        "service_name": (
            log.get("service.name") or 
            log.get("service") or 
            log.get("container.name") or
            "unknown-service"
        ),
        "host_name": (
            log.get("host.name") or 
            log.get("host") or 
            "unknown-host"
        ),
        "error_message": log.get("error.message", ""),
        "error_stack_trace": log.get("error.stack_trace", ""),
        "error_type": log.get("error.type", ""),
        "event_dataset": log.get("event.dataset", ""),
        "event_module": log.get("event.module", ""),
        "raw": log
    }
    normalized_logs.append(normalized)

print(f"  ✓ Normalized {len(normalized_logs)} logs")

# Run analysis pipeline
print("\n[3/4] Running analysis pipeline...")

try:
    from agents.error_parser_agent import ErrorParserAgent
    from agents.rca_analyzer_agent import RCAAnalyzerAgent
    from agents.solution_gen_agent import SolutionGeneratorAgent
    from agents.email_sender_agent import EmailSenderAgent
    
    # Parse errors
    print("  → Parsing errors...")
    parser = ErrorParserAgent()
    parse_result = parser.parse_logs(normalized_logs)
    print(f"    ✓ Found {len(parse_result['error_groups'])} error groups")
    
    # RCA analysis
    print("  → Performing RCA analysis...")
    analyzer = RCAAnalyzerAgent()
    rca_result = analyzer.analyze(
        parse_result["error_groups"],
        parse_result["patterns"],
        parse_result["statistics"]
    )
    print(f"    ✓ Identified {len(rca_result['root_causes'])} root causes")
    
    # Generate solutions
    print("  → Generating solutions...")
    generator = SolutionGeneratorAgent()
    solutions = generator.generate_solutions(
        rca_result,
        parse_result["error_groups"],
        parse_result["statistics"]
    )
    print(f"    ✓ Generated {len(solutions['solutions'])} solutions")
    
    # Send email
    print("\n[4/4] Sending email alert...")
    sender = EmailSenderAgent()
    
    execution_result = {
        "execution_id": datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
        "start_time": datetime.utcnow().isoformat() + "Z"
    }
    
    time_range = f"Production Logs from Kibana ({len(logs)} entries)"
    
    email_sent = sender.send_alert(
        execution_result,
        parse_result["error_groups"],
        rca_result,
        solutions,
        parse_result["statistics"],
        time_range
    )
    
    if email_sent:
        print(f"  ✓ Email alert sent successfully!")
    else:
        print(f"  ⚠ Email sending failed or skipped")
    
    # Save results
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    result_file = results_dir / f"kibana_analysis_{execution_result['execution_id']}.json"
    with open(result_file, 'w') as f:
        json.dump({
            "execution": execution_result,
            "source": "kibana_csv",
            "csv_file": str(csv_file),
            "parse_result": parse_result,
            "rca_result": rca_result,
            "solutions": solutions
        }, f, indent=2, default=str)
    
    print(f"  ✓ Results saved to: {result_file}")
    
    # Print summary
    print("\n" + "="*80)
    print("✓ ANALYSIS COMPLETED SUCCESSFULLY!")
    print("="*80)
    print(f"\nSummary:")
    print(f"  • Logs analyzed: {len(logs)}")
    print(f"  • CSV file: {csv_file}")
    print(f"  • Error groups: {len(parse_result['error_groups'])}")
    print(f"  • Root causes: {len(rca_result['root_causes'])}")
    print(f"  • Solutions: {len(solutions['solutions'])}")
    print(f"  • Email sent: {'Yes' if email_sent else 'No'}")
    print(f"  • Results: {result_file}")
    
    # Show top errors
    if parse_result['error_groups']:
        print(f"\nTop Error Groups:")
        for i, group in enumerate(parse_result['error_groups'][:5], 1):
            print(f"  {i}. {group['service_name']} - {group['error_type']} ({group['count']} occurrences)")
    
    # Show root causes
    if rca_result['root_causes']:
        print(f"\nRoot Causes:")
        for i, cause in enumerate(rca_result['root_causes'][:3], 1):
            desc = cause.get('description', 'Unknown')[:80]
            print(f"  {i}. {desc} (confidence: {cause.get('confidence', 0):.0f}%)")
    
    print("\n" + "="*80)
    
except Exception as e:
    print(f"\n✗ Analysis failed: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
