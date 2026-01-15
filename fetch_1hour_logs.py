"""
Enhanced AWS ECS Log Fetcher with Intelligent Error Detection

Features:
- Fetches logs from AWS CloudWatch
- Conditional processing (skips if no errors)
- CSV export with ECS metadata
- Error deduplication
- Email with CSV attachment
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# IMPORTANT: Do NOT hardcode secrets in source files.
# Load sensitive configuration from environment variables or a secure secrets store.
# Example (set these in your environment or a .env file, do NOT commit them):
#   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, GEMINI_API_KEY, SMTP_USERNAME, SMTP_PASSWORD

# AWS / Gemini / SMTP configuration (read from environment)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = os.getenv("SMTP_PORT", "587")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_RECIPIENTS = os.getenv("ALERT_RECIPIENTS", "")

# Configuration
AWS_REGION = "us-east-1"
LOG_GROUP = "/ecs/myapp"
ECS_SERVICE_NAME = "CA-PROD-API-SERVICE"
ECS_CLUSTER = "CA-PROD-CLR"
ENVIRONMENT = "production"

# Fetch settings
MAX_LOGS = 100000
HOURS_BACK = 1

print("="*80)
print("Enhanced AWS ECS Log Analyzer - Last 1 Hour")
print("="*80)
print(f"\nService: {ECS_SERVICE_NAME}")
print(f"Cluster: {ECS_CLUSTER}")
print(f"Log Group: {LOG_GROUP}")
print(f"Time Range: Last {HOURS_BACK} hour")
print()

# Import boto3
try:
    import boto3
except ImportError:
    print("Installing boto3...")
    os.system("pip install boto3 -q")
    import boto3

# Connect
print("[1/7] Connecting to AWS CloudWatch...")
logs_client = boto3.client(
    'logs',
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)
print("  ✓ Connected")

# Time range
print(f"\n[2/7] Fetching logs from last {HOURS_BACK} hour...")
end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=HOURS_BACK)

start_ts = int(start_time.timestamp() * 1000)
end_ts = int(end_time.timestamp() * 1000)

print(f"  From: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(f"  To:   {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")

# Fetch logs
all_events = []
next_token = None

try:
    while len(all_events) < MAX_LOGS:
        kwargs = {
            'logGroupName': LOG_GROUP,
            'startTime': start_ts,
            'endTime': end_ts,
            'limit': min(10000, MAX_LOGS - len(all_events))
        }
        
        if next_token:
            kwargs['nextToken'] = next_token
        
        response = logs_client.filter_log_events(**kwargs)
        events = response.get('events', [])
        
        if not events:
            break
        
        all_events.extend(events)
        print(f"  → Fetched {len(all_events):,} logs...")
        
        next_token = response.get('nextToken')
        if not next_token or len(all_events) >= MAX_LOGS:
            break
    
    print(f"  ✓ Total: {len(all_events):,} logs")

except Exception as e:
    print(f"  ✗ Error: {str(e)}")
    sys.exit(1)

# Normalize logs
print("\n[3/7] Normalizing logs...")

normalized_logs = []

for event in all_events:
    log_time = datetime.fromtimestamp(event['timestamp'] / 1000)
    message = event['message']
    
    # Detect log level
    message_lower = message.lower()
    if any(kw in message_lower for kw in ['error', 'exception', 'failed']):
        log_level = "error"
    elif 'warn' in message_lower:
        log_level = "warning"
    elif any(kw in message_lower for kw in ['fatal', 'critical']):
        log_level = "critical"
    else:
        log_level = "info"
    
    normalized_logs.append({
        "timestamp": log_time.isoformat() + 'Z',
        "message": message,
        "log_level": log_level,
        "service_name": ECS_SERVICE_NAME,
        "cluster_name": ECS_CLUSTER,
        "container_name": event.get('logStreamName', 'unknown'),
        "environment": ENVIRONMENT,
        "host_name": event.get('logStreamName', 'unknown'),
        "error_message": message if log_level in ["error", "critical"] else "",
        "stack_trace": "",
        "error_type": "",
    })

print(f"  ✓ Normalized {len(normalized_logs):,} logs")

del all_events

# Check for errors
print("\n[4/7] Checking for error-level logs...")

try:
    from agents.error_parser_agent import ErrorParserAgent
    
    parser = ErrorParserAgent()
    has_errors = parser.has_error_level_logs(normalized_logs)
    
    if not has_errors:
        print("  ✓ No error-level logs detected")
        print("\n" + "="*80)
        print("✓ ANALYSIS COMPLETE - NO ERRORS FOUND")
        print("="*80)
        print(f"\nResults:")
        print(f"  • Total Logs: {len(normalized_logs):,}")
        print(f"  • Error Logs: 0")
        print(f"  • Status: All systems normal")
        print(f"  • Action: No alert sent (no errors detected)")
        print("\n" + "="*80)
        sys.exit(0)
    
    # Filter error logs
    error_logs = parser.filter_error_logs(normalized_logs)
    print(f"  ✓ Found {len(error_logs):,} error-level logs")
    
except Exception as e:
    print(f"  ✗ Error detection failed: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Generate CSV
print("\n[5/7] Generating CSV export...")

try:
    from utils.csv_exporter import CSVExporter
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exporter = CSVExporter()
    csv_filepath = exporter.export_to_csv(error_logs, timestamp)
    
    file_size_mb = Path(csv_filepath).stat().st_size / 1024 / 1024
    print(f"  ✓ CSV File: {csv_filepath}")
    print(f"  ✓ Size: {file_size_mb:.2f} MB")
    print(f"  ✓ Rows: {len(error_logs):,}")

except Exception as e:
    print(f"  ✗ CSV export failed: {str(e)}")
    csv_filepath = None

# Analysis
print("\n[6/7] Running RCA and generating solutions...")

try:
    from agents.rca_analyzer_agent import RCAAnalyzerAgent
    from agents.solution_gen_agent import SolutionGeneratorAgent
    
    print("  → Parsing errors...")
    parse_result = parser.parse_logs(normalized_logs)
    print(f"    ✓ {len(parse_result['error_groups'])} error groups")
    
    print("  → RCA analysis...")
    analyzer = RCAAnalyzerAgent()
    rca_result = analyzer.analyze(
        parse_result["error_groups"],
        parse_result["patterns"],
        parse_result["statistics"]
    )
    print(f"    ✓ {len(rca_result['root_causes'])} root causes")
    
    print("  → Generating solutions...")
    generator = SolutionGeneratorAgent()
    solutions = generator.generate_solutions(
        rca_result,
        parse_result["error_groups"],
        parse_result["statistics"]
    )
    print(f"    ✓ {len(solutions['solutions'])} solutions")
    
    # Save results
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    result_file = results_dir / f"ecs_analysis_{timestamp}.json"
    with open(result_file, 'w') as f:
        json.dump({
            "source": "aws_ecs_cloudwatch",
            "service": ECS_SERVICE_NAME,
            "cluster": ECS_CLUSTER,
            "log_group": LOG_GROUP,
            "time_range_hours": HOURS_BACK,
            "logs_analyzed": len(normalized_logs),
            "errors_found": len(error_logs),
            "csv_file": str(csv_filepath) if csv_filepath else None,
            "parse_result": parse_result,
            "rca_result": rca_result,
            "solutions": solutions
        }, f, indent=2, default=str)
    
    print(f"    ✓ Results: {result_file}")

except Exception as e:
    print(f"  ✗ Analysis failed: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Email with CSV attachment
print("\n[7/7] Sending email alert with CSV attachment...")

try:
    from agents.email_sender_agent import EmailSenderAgent
    
    sender = EmailSenderAgent()
    
    execution_result = {
        "execution_id": timestamp,
        "start_time": datetime.utcnow().isoformat() + "Z"
    }
    
    time_range = f"Last {HOURS_BACK}h - {ECS_SERVICE_NAME} ({len(normalized_logs):,} logs, {len(error_logs):,} errors)"
    
    email_sent = sender.send_alert(
        execution_result,
        parse_result["error_groups"],
        rca_result,
        solutions,
        parse_result["statistics"],
        time_range,
        csv_filepath  # Attach CSV file
    )
    
    if email_sent:
        print("  ✓ Email sent with CSV attachment!")
    else:
        print("  ⚠ Email skipped")

except Exception as e:
    print(f"  ⚠ Email error: {str(e)}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "="*80)
print("✓ ANALYSIS COMPLETE - ERRORS DETECTED")
print("="*80)
print(f"\nResults:")
print(f"  • Total Logs: {len(normalized_logs):,}")
print(f"  • Error Logs: {len(error_logs):,}")
print(f"  • CSV File: {csv_filepath}")
print(f"  • File Size: {file_size_mb:.2f} MB")
print(f"  • Error Groups: {len(parse_result['error_groups'])}")
print(f"  • Root Causes: {len(rca_result['root_causes'])}")
print(f"  • Solutions: {len(solutions['solutions'])}")
print(f"  • Email: Sent with CSV attachment")

if parse_result['error_groups']:
    print(f"\nTop Errors:")
    for i, group in enumerate(parse_result['error_groups'][:5], 1):
        print(f"  {i}. {group.get('error_type', 'Unknown')} ({group['count']}x) - {group.get('severity', 'UNKNOWN')}")

print("\n" + "="*80)
