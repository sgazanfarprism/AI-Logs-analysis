"""
Simple E2E Test Runner - No Colors
"""

import sys
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("="*80)
print("AI Log Analysis System - End-to-End Pipeline Test (Simple)")
print("="*80)

try:
    print("\n[Stage 1] Generating Mock Data...")
    from test_e2e_pipeline import E2EPipelineTester
    
    tester = E2EPipelineTester(use_mock_data=True)
    
    # Generate mock logs
    mock_logs = tester.generate_mock_logs(count=20)
    print(f"Generated {len(mock_logs)} mock logs")
    
    print("\n[Stage 2] Testing Log Fetcher...")
    logs = tester.test_log_fetcher(mock_logs=mock_logs)
    print(f"Fetched {len(logs)} logs")
    
    print("\n[Stage 3] Testing Error Parser...")
    parse_result = tester.test_error_parser(logs)
    print(f"Found {len(parse_result['error_groups'])} error groups")
    
    print("\n[Stage 4] Testing RCA Analyzer...")
    rca_result = tester.test_rca_analyzer(parse_result)
    print(f"Identified {len(rca_result['root_causes'])} root causes")
    
    print("\n[Stage 5] Testing Solution Generator...")
    solutions = tester.test_solution_generator(rca_result, parse_result)
    print(f"Generated {len(solutions['solutions'])} solutions")
    
    print("\n[Stage 6] Testing Email Sender (dry run)...")
    email_sent = tester.test_email_sender(parse_result, rca_result, solutions, skip_send=True)
    print(f"Email test: {'Success' if email_sent else 'Failed'}")
    
    print("\n" + "="*80)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("="*80)
    
    # Print summary
    print("\nSummary:")
    for stage_name, stage_data in tester.test_results["stages"].items():
        print(f"  {stage_name}: {stage_data['status']}")
    
except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
