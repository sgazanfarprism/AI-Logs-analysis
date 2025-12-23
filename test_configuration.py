"""
Configuration Test Suite for AI Log Analysis System
Tests all environment variables and connections
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

def test_env_file():
    """Test if .env file exists and can be loaded"""
    print_header("1. Environment File Check")
    
    env_path = Path('.env')
    if not env_path.exists():
        print_error(".env file not found!")
        print_info("Run: cp .env.example .env")
        return False
    
    print_success(".env file exists")
    
    # Load environment variables
    load_dotenv()
    print_success("Environment variables loaded")
    return True

def test_elasticsearch_config():
    """Test Elasticsearch configuration"""
    print_header("2. Elasticsearch Configuration")
    
    required_vars = {
        'ES_HOST': 'Elasticsearch host',
        'ES_PORT': 'Elasticsearch port',
        'ES_USERNAME': 'Elasticsearch username',
        'ES_PASSWORD': 'Elasticsearch password',
        'ES_INDEX_PATTERN': 'Index pattern',
        'ES_USE_SSL': 'SSL setting'
    }
    
    all_present = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive data
            if 'PASSWORD' in var:
                display_value = '*' * len(value)
            else:
                display_value = value
            print_success(f"{description}: {display_value}")
        else:
            print_error(f"{description} ({var}) not set!")
            all_present = False
    
    # Check index pattern
    index_pattern = os.getenv('ES_INDEX_PATTERN', '')
    expected_patterns = ['ecs-logs-prod-*', 'ecs-logs-uat-*', 'aks-logs-prod-*', 'aks-logs-uat-*']
    
    if index_pattern:
        patterns = [p.strip() for p in index_pattern.split(',')]
        print_info(f"Found {len(patterns)} index pattern(s):")
        for pattern in patterns:
            if pattern in expected_patterns:
                print_success(f"  - {pattern}")
            else:
                print_warning(f"  - {pattern} (unexpected)")
    
    return all_present

def test_aws_config():
    """Test AWS CloudWatch configuration"""
    print_header("3. AWS CloudWatch Configuration")
    
    required_vars = {
        'AWS_ACCESS_KEY_ID': 'AWS Access Key ID',
        'AWS_SECRET_ACCESS_KEY': 'AWS Secret Access Key',
        'AWS_REGION_PROD': 'PROD Region',
        'AWS_REGION_UAT': 'UAT Region',
        'AWS_CLOUDWATCH_LOG_GROUP': 'CloudWatch Log Group',
        'AWS_CLOUDWATCH_SCAN_FREQUENCY': 'Scan Frequency',
        'AWS_CLOUDWATCH_START_POSITION': 'Start Position'
    }
    
    all_present = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive data
            if 'SECRET' in var:
                display_value = '*' * len(value)
            elif 'ACCESS_KEY_ID' in var:
                display_value = value[:10] + '...' if len(value) > 10 else value
            else:
                display_value = value
            print_success(f"{description}: {display_value}")
        else:
            print_error(f"{description} ({var}) not set!")
            all_present = False
    
    # Security check
    access_key = os.getenv('AWS_ACCESS_KEY_ID', '')
    if access_key == 'AKIA5FTY6MVKMNMHA6E4':
        print_error("SECURITY WARNING: Using exposed credentials from filebeat.yml!")
        print_warning("These credentials MUST be rotated immediately!")
        all_present = False
    elif access_key == 'your-aws-access-key-id':
        print_warning("Using placeholder credentials - update with real values")
    
    return all_present

def test_aks_config():
    """Test AKS log paths configuration"""
    print_header("4. AKS Log Paths Configuration")
    
    required_vars = {
        'AKS_LOGS_PROD_PATH': 'PROD Log Path',
        'AKS_LOGS_UAT_PATH': 'UAT Log Path',
        'AKS_LOGS_PROD_PATTERN': 'PROD Pattern',
        'AKS_LOGS_UAT_PATTERN': 'UAT Pattern',
        'AKS_MULTILINE_PATTERN': 'Multiline Pattern',
        'AKS_MULTILINE_NEGATE': 'Multiline Negate',
        'AKS_MULTILINE_MATCH': 'Multiline Match'
    }
    
    all_present = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print_success(f"{description}: {value}")
        else:
            print_error(f"{description} ({var}) not set!")
            all_present = False
    
    return all_present

def test_openai_config():
    """Test OpenAI configuration"""
    print_header("5. OpenAI Configuration")
    
    required_vars = {
        'OPENAI_API_KEY': 'API Key',
        'OPENAI_MODEL': 'Model',
        'OPENAI_TEMPERATURE': 'Temperature',
        'OPENAI_MAX_TOKENS': 'Max Tokens'
    }
    
    all_present = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask API key
            if 'API_KEY' in var:
                if value.startswith('sk-'):
                    display_value = value[:10] + '...' + value[-4:]
                else:
                    display_value = '*' * len(value)
            else:
                display_value = value
            print_success(f"{description}: {display_value}")
        else:
            print_error(f"{description} ({var}) not set!")
            all_present = False
    
    # Check if using placeholder
    api_key = os.getenv('OPENAI_API_KEY', '')
    if api_key == 'sk-your-api-key-here':
        print_warning("Using placeholder API key - update with real value")
    
    return all_present

def test_smtp_config():
    """Test SMTP configuration"""
    print_header("6. SMTP Email Configuration")
    
    required_vars = {
        'SMTP_HOST': 'SMTP Host',
        'SMTP_PORT': 'SMTP Port',
        'SMTP_USERNAME': 'Username',
        'SMTP_PASSWORD': 'Password',
        'SMTP_USE_TLS': 'Use TLS',
        'ALERT_RECIPIENTS': 'Alert Recipients'
    }
    
    all_present = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask password
            if 'PASSWORD' in var:
                display_value = '*' * len(value)
            else:
                display_value = value
            print_success(f"{description}: {display_value}")
        else:
            print_error(f"{description} ({var}) not set!")
            all_present = False
    
    return all_present

def test_elasticsearch_connection():
    """Test actual connection to Elasticsearch"""
    print_header("7. Elasticsearch Connection Test")
    
    try:
        from elasticsearch import Elasticsearch
        
        host = os.getenv('ES_HOST', 'localhost')
        port = os.getenv('ES_PORT', '9200')
        username = os.getenv('ES_USERNAME', 'elastic')
        password = os.getenv('ES_PASSWORD', '')
        use_ssl = os.getenv('ES_USE_SSL', 'false').lower() == 'true'
        
        print_info(f"Connecting to {host}:{port}...")
        
        es = Elasticsearch(
            [f"{'https' if use_ssl else 'http'}://{host}:{port}"],
            basic_auth=(username, password),
            verify_certs=False,
            request_timeout=5
        )
        
        if es.ping():
            print_success("Successfully connected to Elasticsearch!")
            
            # Get cluster info
            info = es.info()
            print_success(f"Cluster: {info['cluster_name']}")
            print_success(f"Version: {info['version']['number']}")
            
            # Check indices
            indices = es.cat.indices(format='json')
            log_indices = [idx for idx in indices if 'logs' in idx['index']]
            
            if log_indices:
                print_success(f"Found {len(log_indices)} log indices:")
                for idx in log_indices[:10]:  # Show first 10
                    print_info(f"  - {idx['index']} ({idx['docs.count']} docs)")
            else:
                print_warning("No log indices found yet (this is normal for new setup)")
            
            return True
        else:
            print_error("Could not ping Elasticsearch")
            return False
            
    except ImportError:
        print_warning("elasticsearch package not installed")
        print_info("Run: pip install elasticsearch")
        return None
    except Exception as e:
        print_error(f"Connection failed: {str(e)}")
        return False

def test_aws_connection():
    """Test AWS CloudWatch connection"""
    print_header("8. AWS CloudWatch Connection Test")
    
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_REGION_PROD', 'us-east-1')
        
        if not access_key or not secret_key:
            print_error("AWS credentials not set")
            return False
        
        if access_key == 'your-aws-access-key-id':
            print_warning("Using placeholder credentials - skipping connection test")
            return None
        
        print_info(f"Testing connection to CloudWatch in {region}...")
        
        client = boto3.client(
            'logs',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Try to describe log groups
        log_group = os.getenv('AWS_CLOUDWATCH_LOG_GROUP', '/ecs/myapp')
        response = client.describe_log_groups(
            logGroupNamePrefix=log_group,
            limit=5
        )
        
        print_success("Successfully connected to AWS CloudWatch!")
        
        if response['logGroups']:
            print_success(f"Found {len(response['logGroups'])} log group(s):")
            for group in response['logGroups']:
                print_info(f"  - {group['logGroupName']}")
        else:
            print_warning(f"No log groups found matching '{log_group}'")
        
        return True
        
    except ImportError:
        print_warning("boto3 package not installed")
        print_info("Run: pip install boto3")
        return None
    except NoCredentialsError:
        print_error("AWS credentials are invalid")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidClientTokenId':
            print_error("AWS Access Key ID is invalid")
        elif error_code == 'SignatureDoesNotMatch':
            print_error("AWS Secret Access Key is invalid")
        else:
            print_error(f"AWS Error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print_error(f"Connection failed: {str(e)}")
        return False

def generate_report(results):
    """Generate final test report"""
    print_header("Test Summary Report")
    
    total_tests = len(results)
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print(f"Total Tests: {total_tests}")
    print_success(f"Passed: {passed}")
    print_error(f"Failed: {failed}")
    if skipped > 0:
        print_warning(f"Skipped: {skipped}")
    
    print(f"\nSuccess Rate: {(passed/total_tests)*100:.1f}%")
    
    # Recommendations
    print_header("Recommendations")
    
    if not results.get('env_file'):
        print_error("1. Create .env file: cp .env.example .env")
    
    if not results.get('aws_config'):
        print_error("2. Update AWS credentials in .env file")
    
    if results.get('aws_connection') is False:
        print_error("3. Verify AWS credentials are correct and have CloudWatch permissions")
    
    if results.get('es_connection') is False:
        print_error("4. Check Elasticsearch is running and accessible")
    
    if results.get('openai_config') is False:
        print_error("5. Add OpenAI API key to .env file")
    
    if results.get('smtp_config') is False:
        print_error("6. Configure SMTP settings in .env file")
    
    # Next steps
    print_header("Next Steps")
    
    if passed == total_tests:
        print_success("All tests passed! Your configuration is ready.")
        print_info("Run the orchestrator: python orchestrator/orchestrator.py --health-check")
    elif passed >= total_tests * 0.7:
        print_warning("Most tests passed. Fix remaining issues before production use.")
    else:
        print_error("Multiple configuration issues detected. Review and fix before proceeding.")

def main():
    """Main test execution"""
    print(f"\n{Colors.BOLD}AI Log Analysis System - Configuration Test Suite{Colors.RESET}")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    # Run all tests
    results['env_file'] = test_env_file()
    
    if results['env_file']:
        results['es_config'] = test_elasticsearch_config()
        results['aws_config'] = test_aws_config()
        results['aks_config'] = test_aks_config()
        results['openai_config'] = test_openai_config()
        results['smtp_config'] = test_smtp_config()
        results['es_connection'] = test_elasticsearch_connection()
        results['aws_connection'] = test_aws_connection()
    else:
        print_error("\nCannot proceed without .env file. Exiting.")
        return 1
    
    # Generate report
    generate_report(results)
    
    # Return exit code
    failed_count = sum(1 for r in results.values() if r is False)
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
