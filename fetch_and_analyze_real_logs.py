"""
Real Log Fetcher and Analyzer

Fetches logs from production Kibana/Elasticsearch instance,
saves them as CSV, runs RCA analysis, generates solutions,
and sends email alerts.
"""

import sys
import os
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

# Load environment
load_dotenv()

# Kibana/Elasticsearch credentials
KIBANA_HOST = "logs.prismxai.com"
KIBANA_USERNAME = "prism-user"
KIBANA_PASSWORD = "PrismView2025!"

# Available indices from Kibana
AVAILABLE_INDICES = [
    "CA-PROD-ECS-LOGS",
    "CA-UAT-ECS-LOGS",
    "AKS PROD Logs",
    "AKS UAT Logs"
]

print("="*80)
print("Real Log Analysis Pipeline")
print("="*80)
print()


def connect_to_elasticsearch():
    """Connect to Elasticsearch/Kibana - try multiple connection methods"""
    print("[1/6] Connecting to Elasticsearch...")
    
    # Try different connection configurations
    configs = [
        {"scheme": "https", "port": 443, "verify_certs": False},
        {"scheme": "https", "port": 9200, "verify_certs": False},
        {"scheme": "http", "port": 80, "verify_certs": False},
        {"scheme": "http", "port": 9200, "verify_certs": False},
    ]
    
    for config in configs:
        try:
            url = f"{config['scheme']}://{KIBANA_HOST}:{config['port']}"
            print(f"  Trying: {url}")
            
            es = Elasticsearch(
                [url],
                basic_auth=(KIBANA_USERNAME, KIBANA_PASSWORD),
                verify_certs=config['verify_certs'],
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test connection
            if es.ping():
                info = es.info()
                print(f"  ✓ Connected successfully!")
                print(f"  ✓ Cluster: {info.get('cluster_name', 'Unknown')}")
                print(f"  ✓ Version: {info.get('version', {}).get('number', 'Unknown')}")
                return es
                
        except Exception as e:
            print(f"  ✗ Failed: {str(e)[:100]}")
            continue
    
    print("  ✗ All connection attempts failed")
    return None


def list_indices(es):
    """List available indices"""
    print("\n[2/6] Listing available indices...")
    
    try:
        indices = es.cat.indices(format='json')
        
        # Filter for log indices
        log_indices = [idx for idx in indices if 'log' in idx['index'].lower()]
        
        if log_indices:
            print(f"  ✓ Found {len(log_indices)} log indices:")
            for idx in log_indices[:10]:  # Show first 10
                print(f"    - {idx['index']} ({idx.get('docs.count', '0')} docs)")
            
            # Return the most recent index
            log_indices.sort(key=lambda x: x['index'], reverse=True)
            return log_indices[0]['index'] if log_indices else None
        else:
            print("  ⚠ No log indices found")
            # Show all indices
            print(f"  Available indices ({len(indices)}):")
            for idx in indices[:10]:
                print(f"    - {idx['index']}")
            return indices[0]['index'] if indices else None
            
    except Exception as e:
        print(f"  ✗ Failed to list indices: {str(e)}")
        return None


def fetch_logs(es, index_name, hours=24, max_logs=1000):
    """Fetch logs from Elasticsearch"""
    print(f"\n[3/6] Fetching logs from index: {index_name}")
    print(f"  Time range: Last {hours} hours")
    print(f"  Max logs: {max_logs}")
    
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Build query - try to find error/warning logs
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": start_time.isoformat(),
                                    "lte": end_time.isoformat()
                                }
                            }
                        }
                    ],
                    "should": [
                        {"match": {"log.level": "error"}},
                        {"match": {"log.level": "ERROR"}},
                        {"match": {"log.level": "warning"}},
                        {"match": {"log.level": "WARNING"}},
                        {"match": {"level": "error"}},
                        {"match": {"level": "ERROR"}},
                        {"match": {"severity": "error"}},
                        {"match": {"severity": "ERROR"}}
                    ],
                    "minimum_should_match": 0  # Get all logs if no level field
                }
            },
            "sort": [
                {"@timestamp": {"order": "desc"}}
            ],
            "size": max_logs
        }
        
        # Execute search
        response = es.search(index=index_name, body=query)
        
        hits = response['hits']['hits']
        total = response['hits']['total']['value'] if isinstance(response['hits']['total'], dict) else response['hits']['total']
        
        print(f"  ✓ Found {total} total logs")
        print(f"  ✓ Retrieved {len(hits)} logs")
        
        # Extract log data
        logs = []
        for hit in hits:
            source = hit['_source']
            logs.append(source)
        
        return logs
        
    except Exception as e:
        print(f"  ✗ Failed to fetch logs: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def save_logs_to_csv(logs, output_dir="logs"):
    """Save logs to CSV file"""
    print(f"\n[4/6] Saving logs to CSV...")
    
    try:
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = output_path / f"fetched_logs_{timestamp}.csv"
        
        if not logs:
            print("  ⚠ No logs to save")
            return None
        
        # Determine all unique fields
        all_fields = set()
        for log in logs:
            all_fields.update(flatten_dict(log).keys())
        
        # Common fields to prioritize
        priority_fields = [
            '@timestamp', 'timestamp', 'message', 'log.level', 'level', 
            'severity', 'service.name', 'service', 'host.name', 'host',
            'error.message', 'error.type', 'error.stack_trace'
        ]
        
        # Order fields: priority first, then alphabetically
        ordered_fields = []
        for field in priority_fields:
            if field in all_fields:
                ordered_fields.append(field)
                all_fields.remove(field)
        ordered_fields.extend(sorted(all_fields))
        
        # Write CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=ordered_fields, extrasaction='ignore')
            writer.writeheader()
            
            for log in logs:
                flat_log = flatten_dict(log)
                writer.writerow(flat_log)
        
        print(f"  ✓ Saved {len(logs)} logs to: {csv_file}")
        print(f"  ✓ Fields: {len(ordered_fields)}")
        
        return csv_file
        
    except Exception as e:
        print(f"  ✗ Failed to save CSV: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def flatten_dict(d, parent_key='', sep='.'):
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Convert list to string
            items.append((new_key, json.dumps(v)))
        else:
            items.append((new_key, v))
    return dict(items)


def normalize_logs_for_analysis(logs):
    """Normalize logs for our analysis pipeline"""
    print(f"\n[5/6] Normalizing logs for analysis...")
    
    normalized = []
    
    for log in logs:
        # Try to extract standard fields
        normalized_log = {
            "timestamp": log.get("@timestamp") or log.get("timestamp", datetime.utcnow().isoformat()),
            "message": log.get("message", ""),
            "log_level": (
                log.get("log", {}).get("level") or 
                log.get("level") or 
                log.get("severity") or 
                "info"
            ),
            "service_name": (
                log.get("service", {}).get("name") or 
                log.get("service") or 
                "unknown-service"
            ),
            "host_name": (
                log.get("host", {}).get("name") or 
                log.get("host") or 
                "unknown-host"
            ),
            "error_message": log.get("error", {}).get("message", ""),
            "error_stack_trace": log.get("error", {}).get("stack_trace", ""),
            "error_type": log.get("error", {}).get("type", ""),
            "event_dataset": log.get("event", {}).get("dataset", ""),
            "event_module": log.get("event", {}).get("module", ""),
            "raw": log
        }
        
        normalized.append(normalized_log)
    
    print(f"  ✓ Normalized {len(normalized)} logs")
    return normalized


def run_analysis_pipeline(logs):
    """Run the complete analysis pipeline"""
    print(f"\n[6/6] Running analysis pipeline...")
    
    try:
        # Import agents
        from agents.error_parser_agent import ErrorParserAgent
        from agents.rca_analyzer_agent import RCAAnalyzerAgent
        from agents.solution_gen_agent import SolutionGeneratorAgent
        from agents.email_sender_agent import EmailSenderAgent
        
        # Parse errors
        print("  → Parsing errors...")
        parser = ErrorParserAgent()
        parse_result = parser.parse_logs(logs)
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
        print("  → Sending email alert...")
        sender = EmailSenderAgent()
        
        execution_result = {
            "execution_id": datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
            "start_time": datetime.utcnow().isoformat() + "Z"
        }
        
        time_range = f"Last 24 hours (Production Logs)"
        
        email_sent = sender.send_alert(
            execution_result,
            parse_result["error_groups"],
            rca_result,
            solutions,
            parse_result["statistics"],
            time_range
        )
        
        if email_sent:
            print(f"    ✓ Email alert sent successfully")
        else:
            print(f"    ⚠ Email sending failed or skipped")
        
        # Save results
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        result_file = results_dir / f"analysis_{execution_result['execution_id']}.json"
        with open(result_file, 'w') as f:
            json.dump({
                "execution": execution_result,
                "parse_result": parse_result,
                "rca_result": rca_result,
                "solutions": solutions
            }, f, indent=2, default=str)
        
        print(f"    ✓ Results saved to: {result_file}")
        
        return {
            "parse_result": parse_result,
            "rca_result": rca_result,
            "solutions": solutions,
            "email_sent": email_sent
        }
        
    except Exception as e:
        print(f"  ✗ Analysis pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main execution"""
    
    # Step 1: Connect to Elasticsearch
    es = connect_to_elasticsearch()
    if not es:
        print("\n✗ Failed to connect to Elasticsearch. Exiting.")
        return 1
    
    # Step 2: List and select index
    index_name = list_indices(es)
    if not index_name:
        print("\n✗ No indices found. Exiting.")
        return 1
    
    # Step 3: Fetch logs
    logs = fetch_logs(es, index_name, hours=24, max_logs=1000)
    if not logs:
        print("\n✗ No logs fetched. Exiting.")
        return 1
    
    # Step 4: Save to CSV
    csv_file = save_logs_to_csv(logs)
    
    # Step 5: Normalize logs
    normalized_logs = normalize_logs_for_analysis(logs)
    
    # Step 6: Run analysis
    results = run_analysis_pipeline(normalized_logs)
    
    if results:
        print("\n" + "="*80)
        print("✓ ANALYSIS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"\nSummary:")
        print(f"  • Logs fetched: {len(logs)}")
        print(f"  • CSV saved: {csv_file}")
        print(f"  • Error groups: {len(results['parse_result']['error_groups'])}")
        print(f"  • Root causes: {len(results['rca_result']['root_causes'])}")
        print(f"  • Solutions: {len(results['solutions']['solutions'])}")
        print(f"  • Email sent: {'Yes' if results['email_sent'] else 'No'}")
        print("\n" + "="*80)
        return 0
    else:
        print("\n✗ Analysis failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
