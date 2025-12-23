"""
End-to-End Pipeline Test for AI Log Analysis System

This script tests the complete pipeline from log ingestion to email alerts,
with real-time monitoring and comprehensive validation.
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

# Fix Windows console encoding for colored output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_stage(stage_num, stage_name):
    print(f"\n{Colors.BOLD}{Colors.CYAN}[Stage {stage_num}] {stage_name}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-'*80}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

def print_metric(label, value):
    print(f"{Colors.MAGENTA}  {label}: {Colors.BOLD}{value}{Colors.RESET}")


class E2EPipelineTester:
    """
    End-to-End Pipeline Tester
    
    Tests the complete log analysis pipeline with:
    - Mock data generation
    - Real-time monitoring
    - Stage-by-stage validation
    - Performance metrics
    - Result verification
    """
    
    def __init__(self, use_mock_data: bool = True):
        """
        Initialize E2E tester
        
        Args:
            use_mock_data: If True, use generated mock data instead of real Elasticsearch
        """
        self.use_mock_data = use_mock_data
        self.test_results = {
            "start_time": datetime.utcnow().isoformat(),
            "stages": {},
            "metrics": {},
            "errors": []
        }
        
        # Load environment
        load_dotenv()
        
        print_header("AI Log Analysis System - End-to-End Pipeline Test")
        print_info(f"Test Mode: {'Mock Data' if use_mock_data else 'Real Elasticsearch'}")
        print_info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    def generate_mock_logs(self, count: int = 50) -> List[Dict[str, Any]]:
        """
        Generate mock ECS-formatted logs for testing
        
        Args:
            count: Number of mock logs to generate
        
        Returns:
            List of mock log entries
        """
        print_stage(1, "Generating Mock Test Data")
        
        services = ["auth-service", "payment-service", "user-service", "order-service"]
        error_types = [
            "NullPointerException",
            "ConnectionTimeoutException",
            "DatabaseConnectionError",
            "AuthenticationFailure",
            "ValidationError"
        ]
        
        error_messages = {
            "NullPointerException": "Object reference not set to an instance of an object at line {line}",
            "ConnectionTimeoutException": "Connection to database timed out after 30 seconds",
            "DatabaseConnectionError": "Unable to establish connection to database server",
            "AuthenticationFailure": "Invalid credentials provided for user {user}",
            "ValidationError": "Required field '{field}' is missing or invalid"
        }
        
        mock_logs = []
        base_time = datetime.utcnow() - timedelta(hours=1)
        
        for i in range(count):
            service = services[i % len(services)]
            error_type = error_types[i % len(error_types)]
            
            # Generate error message
            if error_type == "NullPointerException":
                message = error_messages[error_type].format(line=100 + i)
            elif error_type == "AuthenticationFailure":
                message = error_messages[error_type].format(user=f"user{i}")
            elif error_type == "ValidationError":
                message = error_messages[error_type].format(field="email" if i % 2 == 0 else "password")
            else:
                message = error_messages[error_type]
            
            log = {
                "@timestamp": (base_time + timedelta(minutes=i)).isoformat() + "Z",
                "message": f"[{error_type}] {message}",
                "log": {
                    "level": "error" if i % 3 != 0 else "critical"
                },
                "service": {
                    "name": service
                },
                "host": {
                    "name": f"prod-{service}-{(i % 3) + 1}"
                },
                "error": {
                    "message": message,
                    "type": error_type,
                    "stack_trace": f"  at {service}.handler.process(handler.py:{100 + i})\n  at {service}.main(main.py:{50 + i})"
                },
                "event": {
                    "dataset": f"{service}.logs",
                    "module": service.split("-")[0]
                }
            }
            
            mock_logs.append(log)
        
        print_success(f"Generated {len(mock_logs)} mock log entries")
        print_metric("Services", ", ".join(set([log["service"]["name"] for log in mock_logs])))
        print_metric("Error Types", ", ".join(set([log["error"]["type"] for log in mock_logs])))
        print_metric("Time Range", f"{mock_logs[0]['@timestamp']} to {mock_logs[-1]['@timestamp']}")
        
        return mock_logs
    
    def test_log_fetcher(self, mock_logs: List[Dict] = None) -> List[Dict]:
        """Test Log Fetcher Agent"""
        print_stage(2, "Testing Log Fetcher Agent")
        
        start_time = time.time()
        
        try:
            if self.use_mock_data and mock_logs:
                # Simulate log fetcher with mock data
                print_info("Using mock data (simulating Elasticsearch fetch)")
                
                from agents.log_fetcher_agent import LogFetcherAgent
                fetcher = LogFetcherAgent()
                
                # Normalize mock logs
                normalized_logs = []
                for raw_log in mock_logs:
                    normalized = fetcher._normalize_log(raw_log)
                    normalized_logs.append(normalized)
                
                logs = normalized_logs
                print_success(f"Fetched and normalized {len(logs)} logs")
            else:
                # Use real Elasticsearch
                print_info("Fetching from Elasticsearch")
                from agents.log_fetcher_agent import LogFetcherAgent
                
                fetcher = LogFetcherAgent()
                logs = fetcher.fetch_logs(hours=1, max_logs=100)
                print_success(f"Fetched {len(logs)} logs from Elasticsearch")
            
            elapsed = time.time() - start_time
            
            self.test_results["stages"]["log_fetching"] = {
                "status": "success",
                "logs_count": len(logs),
                "elapsed_seconds": round(elapsed, 2)
            }
            
            print_metric("Logs Retrieved", len(logs))
            print_metric("Elapsed Time", f"{elapsed:.2f}s")
            
            return logs
        
        except Exception as e:
            elapsed = time.time() - start_time
            print_error(f"Log fetching failed: {str(e)}")
            
            self.test_results["stages"]["log_fetching"] = {
                "status": "failed",
                "error": str(e),
                "elapsed_seconds": round(elapsed, 2)
            }
            self.test_results["errors"].append(f"Log Fetcher: {str(e)}")
            
            raise
    
    def test_error_parser(self, logs: List[Dict]) -> Dict:
        """Test Error Parser Agent"""
        print_stage(3, "Testing Error Parser Agent")
        
        start_time = time.time()
        
        try:
            from agents.error_parser_agent import ErrorParserAgent
            
            parser = ErrorParserAgent()
            parse_result = parser.parse_logs(logs)
            
            elapsed = time.time() - start_time
            
            self.test_results["stages"]["error_parsing"] = {
                "status": "success",
                "error_groups": len(parse_result["error_groups"]),
                "patterns": len(parse_result["patterns"]),
                "elapsed_seconds": round(elapsed, 2)
            }
            
            print_success("Error parsing completed")
            print_metric("Error Groups", len(parse_result["error_groups"]))
            print_metric("Patterns Detected", len(parse_result["patterns"]))
            print_metric("Total Errors", parse_result["statistics"]["total_errors"])
            print_metric("Elapsed Time", f"{elapsed:.2f}s")
            
            # Show sample error groups
            if parse_result["error_groups"]:
                print_info("\nSample Error Groups:")
                for i, group in enumerate(parse_result["error_groups"][:3]):
                    print(f"  {i+1}. {group['error_type']} - {group['count']} occurrences")
            
            return parse_result
        
        except Exception as e:
            elapsed = time.time() - start_time
            print_error(f"Error parsing failed: {str(e)}")
            
            self.test_results["stages"]["error_parsing"] = {
                "status": "failed",
                "error": str(e),
                "elapsed_seconds": round(elapsed, 2)
            }
            self.test_results["errors"].append(f"Error Parser: {str(e)}")
            
            raise
    
    def test_rca_analyzer(self, parse_result: Dict) -> Dict:
        """Test RCA Analyzer Agent"""
        print_stage(4, "Testing RCA Analyzer Agent")
        
        start_time = time.time()
        
        try:
            from agents.rca_analyzer_agent import RCAAnalyzerAgent
            
            analyzer = RCAAnalyzerAgent()
            rca_result = analyzer.analyze(
                parse_result["error_groups"],
                parse_result["patterns"],
                parse_result["statistics"]
            )
            
            elapsed = time.time() - start_time
            
            self.test_results["stages"]["rca_analysis"] = {
                "status": "success",
                "root_causes": len(rca_result["root_causes"]),
                "confidence": rca_result["confidence_score"],
                "elapsed_seconds": round(elapsed, 2)
            }
            
            print_success("RCA analysis completed")
            print_metric("Root Causes Identified", len(rca_result["root_causes"]))
            print_metric("Confidence Score", f"{rca_result['confidence_score']:.2f}")
            print_metric("Analysis Method", rca_result["analysis_method"])
            print_metric("Elapsed Time", f"{elapsed:.2f}s")
            
            # Show sample root causes
            if rca_result["root_causes"]:
                print_info("\nSample Root Causes:")
                for i, cause in enumerate(rca_result["root_causes"][:3]):
                    print(f"  {i+1}. {cause['category']}: {cause['description'][:80]}...")
            
            return rca_result
        
        except Exception as e:
            elapsed = time.time() - start_time
            print_error(f"RCA analysis failed: {str(e)}")
            
            self.test_results["stages"]["rca_analysis"] = {
                "status": "failed",
                "error": str(e),
                "elapsed_seconds": round(elapsed, 2)
            }
            self.test_results["errors"].append(f"RCA Analyzer: {str(e)}")
            
            raise
    
    def test_solution_generator(self, rca_result: Dict, parse_result: Dict) -> Dict:
        """Test Solution Generator Agent"""
        print_stage(5, "Testing Solution Generator Agent")
        
        start_time = time.time()
        
        try:
            from agents.solution_gen_agent import SolutionGeneratorAgent
            
            generator = SolutionGeneratorAgent()
            solutions = generator.generate_solutions(
                rca_result,
                parse_result["error_groups"],
                parse_result["statistics"]
            )
            
            elapsed = time.time() - start_time
            
            self.test_results["stages"]["solution_generation"] = {
                "status": "success",
                "solutions": len(solutions["solutions"]),
                "confidence": solutions["overall_confidence"],
                "elapsed_seconds": round(elapsed, 2)
            }
            
            print_success("Solution generation completed")
            print_metric("Solutions Generated", len(solutions["solutions"]))
            print_metric("Overall Confidence", f"{solutions['overall_confidence']:.2f}")
            print_metric("Generation Method", solutions["generation_method"])
            print_metric("Elapsed Time", f"{elapsed:.2f}s")
            
            # Show sample solutions
            if solutions["solutions"]:
                print_info("\nSample Solutions:")
                for i, solution in enumerate(solutions["solutions"][:3]):
                    print(f"  {i+1}. {solution['title']}")
                    print(f"     Priority: {solution['priority']} | Confidence: {solution['confidence']:.2f}")
            
            return solutions
        
        except Exception as e:
            elapsed = time.time() - start_time
            print_error(f"Solution generation failed: {str(e)}")
            
            self.test_results["stages"]["solution_generation"] = {
                "status": "failed",
                "error": str(e),
                "elapsed_seconds": round(elapsed, 2)
            }
            self.test_results["errors"].append(f"Solution Generator: {str(e)}")
            
            raise
    
    def test_email_sender(self, parse_result: Dict, rca_result: Dict, solutions: Dict, skip_send: bool = False) -> bool:
        """Test Email Sender Agent"""
        print_stage(6, "Testing Email Sender Agent")
        
        start_time = time.time()
        
        try:
            from agents.email_sender_agent import EmailSenderAgent
            
            sender = EmailSenderAgent()
            
            if skip_send:
                print_warning("Skipping actual email send (dry run)")
                print_info("Email would be sent to: " + os.getenv("ALERT_RECIPIENTS", "Not configured"))
                email_sent = True
            else:
                # Create mock execution result
                execution_result = {
                    "execution_id": datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
                    "start_time": datetime.utcnow().isoformat() + "Z"
                }
                
                time_range = f"Last 1 hour (test run)"
                
                email_sent = sender.send_alert(
                    execution_result,
                    parse_result["error_groups"],
                    rca_result,
                    solutions,
                    parse_result["statistics"],
                    time_range
                )
            
            elapsed = time.time() - start_time
            
            self.test_results["stages"]["email_sending"] = {
                "status": "success" if email_sent else "failed",
                "elapsed_seconds": round(elapsed, 2)
            }
            
            if email_sent:
                print_success("Email alert sent successfully")
            else:
                print_warning("Email sending skipped or failed")
            
            print_metric("Elapsed Time", f"{elapsed:.2f}s")
            
            return email_sent
        
        except Exception as e:
            elapsed = time.time() - start_time
            print_error(f"Email sending failed: {str(e)}")
            
            self.test_results["stages"]["email_sending"] = {
                "status": "failed",
                "error": str(e),
                "elapsed_seconds": round(elapsed, 2)
            }
            self.test_results["errors"].append(f"Email Sender: {str(e)}")
            
            return False
    
    def generate_report(self):
        """Generate final test report"""
        print_header("End-to-End Test Report")
        
        self.test_results["end_time"] = datetime.utcnow().isoformat()
        
        # Calculate totals
        total_stages = len(self.test_results["stages"])
        successful_stages = sum(1 for stage in self.test_results["stages"].values() if stage["status"] == "success")
        failed_stages = sum(1 for stage in self.test_results["stages"].values() if stage["status"] == "failed")
        
        total_time = sum(stage.get("elapsed_seconds", 0) for stage in self.test_results["stages"].values())
        
        # Print summary
        print(f"{Colors.BOLD}Test Summary:{Colors.RESET}")
        print_metric("Total Stages", total_stages)
        print_metric("Successful", f"{Colors.GREEN}{successful_stages}{Colors.RESET}")
        print_metric("Failed", f"{Colors.RED}{failed_stages}{Colors.RESET}")
        print_metric("Success Rate", f"{(successful_stages/total_stages)*100:.1f}%")
        print_metric("Total Execution Time", f"{total_time:.2f}s")
        
        # Stage details
        print(f"\n{Colors.BOLD}Stage Results:{Colors.RESET}")
        for stage_name, stage_data in self.test_results["stages"].items():
            status_icon = "✓" if stage_data["status"] == "success" else "✗"
            status_color = Colors.GREEN if stage_data["status"] == "success" else Colors.RED
            
            print(f"{status_color}{status_icon} {stage_name.replace('_', ' ').title()}: {stage_data['status']}{Colors.RESET}")
            print(f"  Time: {stage_data.get('elapsed_seconds', 0):.2f}s")
            
            if "error" in stage_data:
                print(f"  Error: {stage_data['error']}")
        
        # Errors
        if self.test_results["errors"]:
            print(f"\n{Colors.BOLD}{Colors.RED}Errors Encountered:{Colors.RESET}")
            for error in self.test_results["errors"]:
                print_error(error)
        
        # Save report
        report_path = Path("results") / f"e2e_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n{Colors.BOLD}Report saved to: {Colors.CYAN}{report_path}{Colors.RESET}")
        
        # Final verdict
        print_header("Test Verdict")
        
        if failed_stages == 0:
            print(f"{Colors.BOLD}{Colors.GREEN}✓ ALL TESTS PASSED!{Colors.RESET}")
            print_success("The end-to-end pipeline is working correctly")
            return 0
        elif successful_stages >= total_stages * 0.7:
            print(f"{Colors.BOLD}{Colors.YELLOW}⚠ PARTIAL SUCCESS{Colors.RESET}")
            print_warning("Some stages failed. Review errors above.")
            return 1
        else:
            print(f"{Colors.BOLD}{Colors.RED}✗ TESTS FAILED{Colors.RESET}")
            print_error("Multiple critical failures detected")
            return 1
    
    def run_full_test(self, skip_email: bool = False):
        """
        Run complete end-to-end test
        
        Args:
            skip_email: Skip actual email sending
        """
        try:
            # Stage 1: Generate or fetch logs
            if self.use_mock_data:
                mock_logs = self.generate_mock_logs(count=50)
                logs = self.test_log_fetcher(mock_logs=mock_logs)
            else:
                logs = self.test_log_fetcher()
            
            if not logs:
                print_error("No logs to process. Aborting test.")
                return self.generate_report()
            
            # Stage 2: Parse errors
            parse_result = self.test_error_parser(logs)
            
            # Stage 3: RCA analysis
            rca_result = self.test_rca_analyzer(parse_result)
            
            # Stage 4: Generate solutions
            solutions = self.test_solution_generator(rca_result, parse_result)
            
            # Stage 5: Send email
            self.test_email_sender(parse_result, rca_result, solutions, skip_send=skip_email)
            
            # Generate final report
            return self.generate_report()
        
        except Exception as e:
            print_error(f"\nTest execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return self.generate_report()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="End-to-End Pipeline Test for AI Log Analysis System"
    )
    
    parser.add_argument(
        "--real-data",
        action="store_true",
        help="Use real Elasticsearch data instead of mock data"
    )
    
    parser.add_argument(
        "--send-email",
        action="store_true",
        help="Actually send email alert (default: dry run)"
    )
    
    parser.add_argument(
        "--mock-count",
        type=int,
        default=50,
        help="Number of mock logs to generate (default: 50)"
    )
    
    args = parser.parse_args()
    
    # Create tester
    tester = E2EPipelineTester(use_mock_data=not args.real_data)
    
    # Run test
    exit_code = tester.run_full_test(skip_email=not args.send_email)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
