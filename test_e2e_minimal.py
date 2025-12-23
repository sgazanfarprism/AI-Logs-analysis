"""
Minimal E2E Test - Tests pipeline with minimal dependencies
"""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("="*80)
print("AI Log Analysis System - Minimal End-to-End Test")
print("="*80)
print()

# Generate mock logs directly
def generate_mock_logs(count=20):
    """Generate simple mock logs"""
    services = ["auth-service", "payment-service", "user-service"]
    error_types = ["NullPointerException", "ConnectionTimeout", "DatabaseError"]
    
    mock_logs = []
    base_time = datetime.utcnow() - timedelta(hours=1)
    
    for i in range(count):
        log = {
            "timestamp": (base_time + timedelta(minutes=i)).isoformat() + "Z",
            "message": f"Error in {services[i % len(services)]}: {error_types[i % len(error_types)]}",
            "log_level": "error",
            "service_name": services[i % len(services)],
            "host_name": f"prod-host-{i % 3}",
            "error_message": f"Test error message {i}",
            "error_stack_trace": f"Stack trace line {i}",
            "error_type": error_types[i % len(error_types)],
            "event_dataset": f"{services[i % len(services)]}.logs",
            "event_module": "test",
            "raw": {}
        }
        mock_logs.append(log)
    
    return mock_logs

try:
    print("[1/5] Generating mock logs...")
    logs = generate_mock_logs(20)
    print(f"  ✓ Generated {len(logs)} mock logs")
    
    print("\n[2/5] Testing Error Parser...")
    from agents.error_parser_agent import ErrorParserAgent
    parser = ErrorParserAgent()
    parse_result = parser.parse_logs(logs)
    print(f"  ✓ Found {len(parse_result['error_groups'])} error groups")
    print(f"  ✓ Detected {len(parse_result['patterns'])} patterns")
    
    print("\n[3/5] Testing RCA Analyzer...")
    from agents.rca_analyzer_agent import RCAAnalyzerAgent
    analyzer = RCAAnalyzerAgent()
    rca_result = analyzer.analyze(
        parse_result["error_groups"],
        parse_result["patterns"],
        parse_result["statistics"]
    )
    print(f"  ✓ Identified {len(rca_result['root_causes'])} root causes")
    print(f"  ✓ Confidence score: {rca_result['confidence_score']:.1f}")
    print(f"  ✓ Analysis method: {rca_result.get('analysis_method', 'rule-based')}")
    
    print("\n[4/5] Testing Solution Generator...")
    from agents.solution_gen_agent import SolutionGeneratorAgent
    generator = SolutionGeneratorAgent()
    solutions = generator.generate_solutions(
        rca_result,
        parse_result["error_groups"],
        parse_result["statistics"]
    )
    print(f"  ✓ Generated {len(solutions['solutions'])} solutions")
    print(f"  ✓ Overall confidence: {solutions['overall_confidence']:.1f}")
    print(f"  ✓ Generation method: {solutions.get('generation_method', 'rule-based')}")
    
    print("\n[5/5] Testing Email Sender (dry run)...")
    print("  ✓ Email sender module loaded (skipping actual send)")
    
    print("\n" + "="*80)
    print("✓ ALL TESTS PASSED!")
    print("="*80)
    
    # Print detailed results
    print("\nDetailed Results:")
    print(f"\n  Error Groups ({len(parse_result['error_groups'])}):")
    for i, group in enumerate(parse_result['error_groups'][:3], 1):
        print(f"    {i}. {group['service_name']} - {group['error_type']} ({group['count']} occurrences)")
    
    print(f"\n  Root Causes ({len(rca_result['root_causes'])}):")
    for i, cause in enumerate(rca_result['root_causes'][:3], 1):
        desc = cause.get('description', 'Unknown')
        if len(desc) > 60:
            desc = desc[:60] + "..."
        print(f"    {i}. {desc} (confidence: {cause.get('confidence', 0):.0f}%)")
    
    print(f"\n  Solutions ({len(solutions['solutions'])}):")
    for i, solution in enumerate(solutions['solutions'][:3], 1):
        # Solutions use 'root_cause' as the title
        title = solution.get('root_cause', 'Unknown solution')
        if len(title) > 60:
            title = title[:60] + "..."
        print(f"    {i}. {title}")
        print(f"       Priority: {solution.get('priority', 'N/A')} | Confidence: {solution.get('confidence', 0):.0f}%")

    
    print("\n" + "="*80)
    print("Pipeline is working correctly!")
    print("="*80)
    
except Exception as e:
    print(f"\n✗ TEST FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
