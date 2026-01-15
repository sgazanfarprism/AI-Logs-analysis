"""
Test script for enhanced error detection and CSV reporting system

This script tests:
1. CSV export functionality
2. Error detection logic
3. Error signature generation
4. Conditional workflow
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.error_parser_agent import ErrorParserAgent
from utils.csv_exporter import CSVExporter


def test_csv_export():
    """Test CSV export functionality"""
    print("\n" + "="*60)
    print("TEST 1: CSV Export Functionality")
    print("="*60)
    
    test_logs = [
        {
            "timestamp": "2025-12-30T22:00:00Z",
            "log_level": "error",
            "service_name": "user-service",
            "message": "NullPointerException in UserController",
            "error_type": "NullPointerException",
            "stack_trace": "at com.example.UserController.getUser(UserController.java:45)",
            "container_name": "user-service-container",
            "environment": "production",
            "cluster_name": "prod-ecs-cluster"
        },
        {
            "timestamp": "2025-12-30T22:01:00Z",
            "log_level": "critical",
            "service_name": "payment-service",
            "message": "Database connection failed",
            "error_type": "ConnectionTimeout",
            "stack_trace": "at com.example.db.ConnectionPool.getConnection(ConnectionPool.java:123)",
            "container_name": "payment-service-container",
            "environment": "production",
            "cluster_name": "prod-ecs-cluster"
        }
    ]
    
    try:
        exporter = CSVExporter()
        filepath = exporter.export_to_csv(test_logs, "test")
        
        print(f"✅ CSV file created: {filepath}")
        print(f"✅ Exported {len(test_logs)} logs")
        
        # Verify file exists
        if Path(filepath).exists():
            print(f"✅ File exists and is readable")
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"✅ CSV has {len(lines)} lines (including header)")
                print(f"\nFirst 3 lines:")
                for i, line in enumerate(lines[:3], 1):
                    print(f"  {i}: {line.strip()[:100]}...")
        else:
            print(f"❌ File not found: {filepath}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ CSV export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_detection():
    """Test error detection logic"""
    print("\n" + "="*60)
    print("TEST 2: Error Detection Logic")
    print("="*60)
    
    agent = ErrorParserAgent()
    
    # Test 1: No errors
    logs_no_errors = [
        {'message': 'Info log', 'log_level': 'info'},
        {'message': 'Debug message', 'log_level': 'debug'}
    ]
    
    has_errors = agent.has_error_level_logs(logs_no_errors)
    if not has_errors:
        print("✅ Test 1: Correctly identified no errors in info/debug logs")
    else:
        print("❌ Test 1: False positive - detected errors in clean logs")
        return False
    
    # Test 2: With errors
    logs_with_errors = [
        {'message': 'Error occurred', 'log_level': 'error'},
        {'message': 'Exception thrown', 'log_level': 'error', 'error_type': 'NullPointerException'}
    ]
    
    has_errors = agent.has_error_level_logs(logs_with_errors)
    if has_errors:
        print("✅ Test 2: Correctly detected errors in error logs")
    else:
        print("❌ Test 2: False negative - missed errors in error logs")
        return False
    
    # Test 3: Filter errors
    mixed_logs = [
        {'message': 'Info log', 'log_level': 'info'},
        {'message': 'Error occurred', 'log_level': 'error'},
        {'message': 'Debug message', 'log_level': 'debug'},
        {'message': 'Critical failure', 'log_level': 'critical'}
    ]
    
    error_logs = agent.filter_error_logs(mixed_logs)
    if len(error_logs) == 2:
        print(f"✅ Test 3: Correctly filtered {len(error_logs)} error logs from {len(mixed_logs)} total")
    else:
        print(f"❌ Test 3: Expected 2 error logs, got {len(error_logs)}")
        return False
    
    return True


def test_signature_generation():
    """Test error signature generation and deduplication"""
    print("\n" + "="*60)
    print("TEST 3: Error Signature Generation")
    print("="*60)
    
    agent = ErrorParserAgent()
    
    # Test 1: Same error with different line numbers should match
    log1 = {
        'error_type': 'NullPointerException',
        'service_name': 'api-service',
        'error_message': 'null value at line 123'
    }
    
    log2 = {
        'error_type': 'NullPointerException',
        'service_name': 'api-service',
        'error_message': 'null value at line 456'
    }
    
    sig1 = agent.generate_error_signature(log1)
    sig2 = agent.generate_error_signature(log2)
    
    print(f"Signature 1: {sig1}")
    print(f"Signature 2: {sig2}")
    
    if sig1 == sig2:
        print("✅ Test 1: Signatures match (line numbers normalized)")
    else:
        print("❌ Test 1: Signatures don't match (should be identical)")
        return False
    
    # Test 2: Different errors should have different signatures
    log3 = {
        'error_type': 'ConnectionTimeout',
        'service_name': 'api-service',
        'error_message': 'connection timeout'
    }
    
    sig3 = agent.generate_error_signature(log3)
    
    if sig1 != sig3:
        print("✅ Test 2: Different errors have different signatures")
    else:
        print("❌ Test 2: Different errors have same signature")
        return False
    
    return True


def test_conditional_workflow():
    """Test conditional workflow logic"""
    print("\n" + "="*60)
    print("TEST 4: Conditional Workflow")
    print("="*60)
    
    agent = ErrorParserAgent()
    
    # Scenario 1: No errors - should skip processing
    clean_logs = [
        {'message': 'Application started', 'log_level': 'info'},
        {'message': 'Request processed', 'log_level': 'info'}
    ]
    
    if not agent.has_error_level_logs(clean_logs):
        print("✅ Scenario 1: Would skip RCA/alerts for clean logs")
    else:
        print("❌ Scenario 1: Would incorrectly process clean logs")
        return False
    
    # Scenario 2: Has errors - should process
    error_logs = [
        {'message': 'Database connection failed', 'log_level': 'error'},
        {'message': 'Service unavailable', 'log_level': 'critical'}
    ]
    
    if agent.has_error_level_logs(error_logs):
        print("✅ Scenario 2: Would process logs with errors")
    else:
        print("❌ Scenario 2: Would incorrectly skip error logs")
        return False
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ENHANCED ERROR DETECTION SYSTEM - TEST SUITE")
    print("="*60)
    print(f"Test started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    results = []
    
    # Run tests
    results.append(("CSV Export", test_csv_export()))
    results.append(("Error Detection", test_error_detection()))
    results.append(("Signature Generation", test_signature_generation()))
    results.append(("Conditional Workflow", test_conditional_workflow()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready for production use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
