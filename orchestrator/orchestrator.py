"""
Orchestrator

Central coordinator that manages the execution of all agents,
handles scheduling, and provides manual trigger support.
"""

import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import schedule
import time

from agents.log_fetcher_agent import LogFetcherAgent
from agents.error_parser_agent import ErrorParserAgent
from agents.rca_analyzer_agent import RCAAnalyzerAgent
from agents.solution_gen_agent import SolutionGeneratorAgent
from agents.email_sender_agent import EmailSenderAgent

from utils.logger import get_logger
from utils.helpers import parse_time_range, format_timestamp, save_json, ensure_directory
from utils.exceptions import (
    OrchestrationException,
    AgentExecutionError
)

logger = get_logger(__name__)


class Orchestrator:
    """
    Central orchestrator for the Agentic Log Analysis System
    
    Features:
    - Agent coordination
    - Scheduled execution
    - Manual triggers
    - Error handling and recovery
    - Result persistence
    """
    
    def __init__(self):
        """Initialize orchestrator and all agents"""
        logger.info("Initializing Orchestrator")
        
        try:
            self.log_fetcher = LogFetcherAgent()
            self.error_parser = ErrorParserAgent()
            self.rca_analyzer = RCAAnalyzerAgent()
            self.solution_generator = SolutionGeneratorAgent()
            self.email_sender = EmailSenderAgent()
            
            logger.info("All agents initialized successfully")
        
        except Exception as e:
            logger.error("Failed to initialize agents", exc_info=True)
            raise OrchestrationException(
                "Orchestrator initialization failed",
                {"error": str(e)}
            )
    
    def run_analysis(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        hours: Optional[int] = None,
        service_filter: Optional[list] = None,
        severity_filter: Optional[list] = None,
        send_email: bool = True,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run complete log analysis pipeline
        
        Args:
            start_time: Analysis start time
            end_time: Analysis end time
            hours: Hours back from now
            service_filter: Filter by services
            severity_filter: Filter by severity
            send_email: Whether to send email alert
            save_results: Whether to save results to file
        
        Returns:
            Complete analysis result
        
        Raises:
            OrchestrationException: If analysis fails
        """
        execution_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        logger.info(
            "Starting log analysis",
            extra={
                "execution_id": execution_id,
                "hours": hours,
                "service_filter": service_filter,
                "severity_filter": severity_filter
            }
        )
        
        result = {
            "execution_id": execution_id,
            "start_time": datetime.utcnow().isoformat() + "Z",
            "status": "in_progress",
            "stages": {}
        }
        
        try:
            # Stage 1: Fetch Logs
            logger.info("Stage 1: Fetching logs")
            logs = self._execute_stage(
                "log_fetching",
                self.log_fetcher.fetch_logs,
                start_time=start_time,
                end_time=end_time,
                hours=hours,
                service_filter=service_filter,
                severity_filter=severity_filter
            )
            
            result["stages"]["log_fetching"] = {
                "status": "success",
                "logs_count": len(logs)
            }
            
            if not logs:
                logger.warning("No logs found in specified time range")
                result["status"] = "completed_no_logs"
                result["end_time"] = datetime.utcnow().isoformat() + "Z"
                return result
            
            # Stage 2: Parse and Classify Errors
            logger.info("Stage 2: Parsing and classifying errors")
            parse_result = self._execute_stage(
                "error_parsing",
                self.error_parser.parse_logs,
                logs
            )
            
            result["stages"]["error_parsing"] = {
                "status": "success",
                "error_groups": len(parse_result["error_groups"]),
                "patterns": len(parse_result["patterns"])
            }
            
            # Stage 3: Root Cause Analysis
            logger.info("Stage 3: Performing root cause analysis")
            rca_result = self._execute_stage(
                "rca_analysis",
                self.rca_analyzer.analyze,
                parse_result["error_groups"],
                parse_result["patterns"],
                parse_result["statistics"]
            )
            
            result["stages"]["rca_analysis"] = {
                "status": "success",
                "root_causes": len(rca_result["root_causes"]),
                "confidence": rca_result["confidence_score"]
            }
            
            # Stage 4: Generate Solutions
            logger.info("Stage 4: Generating solutions")
            solutions = self._execute_stage(
                "solution_generation",
                self.solution_generator.generate_solutions,
                rca_result,
                parse_result["error_groups"],
                parse_result["statistics"]
            )
            
            result["stages"]["solution_generation"] = {
                "status": "success",
                "solutions": len(solutions["solutions"]),
                "confidence": solutions["overall_confidence"]
            }
            
            # Stage 5: Send Email Alert
            if send_email:
                logger.info("Stage 5: Sending email alert")
                
                # Determine time range for email
                start_dt, end_dt = parse_time_range(start_time, end_time, hours)
                time_range = f"{format_timestamp(start_dt, 'human')} to {format_timestamp(end_dt, 'human')}"
                
                email_sent = self._execute_stage(
                    "email_sending",
                    self.email_sender.send_alert,
                    result,
                    parse_result["error_groups"],
                    rca_result,
                    solutions,
                    parse_result["statistics"],
                    time_range
                )
                
                result["stages"]["email_sending"] = {
                    "status": "success" if email_sent else "failed"
                }
            
            # Save results
            if save_results:
                self._save_results(execution_id, {
                    "metadata": result,
                    "logs": logs,
                    "parse_result": parse_result,
                    "rca_result": rca_result,
                    "solutions": solutions
                })
            
            # Mark as completed
            result["status"] = "completed_success"
            result["end_time"] = datetime.utcnow().isoformat() + "Z"
            
            logger.info(
                "Log analysis completed successfully",
                extra={
                    "execution_id": execution_id,
                    "logs_analyzed": len(logs),
                    "error_groups": len(parse_result["error_groups"]),
                    "root_causes": len(rca_result["root_causes"])
                }
            )
            
            return result
        
        except Exception as e:
            logger.error("Log analysis failed", exc_info=True)
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.utcnow().isoformat() + "Z"
            
            raise OrchestrationException(
                "Log analysis pipeline failed",
                {"execution_id": execution_id, "error": str(e)}
            )
    
    def _execute_stage(self, stage_name: str, func, *args, **kwargs):
        """Execute a pipeline stage with error handling"""
        
        try:
            logger.info(f"Executing stage: {stage_name}")
            result = func(*args, **kwargs)
            logger.info(f"Stage completed: {stage_name}")
            return result
        
        except Exception as e:
            logger.error(f"Stage failed: {stage_name}", exc_info=True)
            raise AgentExecutionError(
                f"Stage execution failed: {stage_name}",
                {"stage": stage_name, "error": str(e)}
            )
    
    def _save_results(self, execution_id: str, results: Dict[str, Any]):
        """Save analysis results to file"""
        
        try:
            results_dir = ensure_directory("results")
            filepath = results_dir / f"analysis_{execution_id}.json"
            save_json(results, filepath)
            
            logger.info(
                "Results saved",
                extra={"filepath": str(filepath)}
            )
        
        except Exception as e:
            logger.warning(f"Failed to save results: {e}")
    
    def schedule_daily_analysis(self, run_time: str = "02:00", hours: int = 24):
        """
        Schedule daily analysis
        
        Args:
            run_time: Time to run (HH:MM format)
            hours: Hours of logs to analyze
        """
        logger.info(
            "Scheduling daily analysis",
            extra={"run_time": run_time, "hours": hours}
        )
        
        def job():
            logger.info("Starting scheduled analysis")
            try:
                self.run_analysis(hours=hours)
            except Exception as e:
                logger.error("Scheduled analysis failed", exc_info=True)
        
        schedule.every().day.at(run_time).do(job)
        
        logger.info(f"Daily analysis scheduled at {run_time}")
        
        # Run scheduler loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all components
        
        Returns:
            Health check results
        """
        logger.info("Performing health check")
        
        health = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "overall_status": "healthy",
            "components": {}
        }
        
        # Check Elasticsearch
        try:
            es_healthy = self.log_fetcher.test_connection()
            health["components"]["elasticsearch"] = {
                "status": "healthy" if es_healthy else "unhealthy"
            }
        except Exception as e:
            health["components"]["elasticsearch"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["overall_status"] = "degraded"
        
        # Check email
        try:
            # Just validate config, don't send test email
            self.email_sender._parse_recipients()
            health["components"]["email"] = {"status": "healthy"}
        except Exception as e:
            health["components"]["email"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["overall_status"] = "degraded"
        
        # Check AI
        try:
            if self.rca_analyzer.ai_client:
                health["components"]["ai"] = {"status": "healthy"}
            else:
                health["components"]["ai"] = {"status": "not_configured"}
        except Exception as e:
            health["components"]["ai"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        logger.info(
            "Health check completed",
            extra={"status": health["overall_status"]}
        )
        
        return health


def main():
    """Main entry point for orchestrator"""
    
    parser = argparse.ArgumentParser(
        description="Agentic AI Log Analysis System Orchestrator"
    )
    
    parser.add_argument(
        "--mode",
        choices=["scheduled", "manual"],
        default="manual",
        help="Execution mode: scheduled (daily) or manual (on-demand)"
    )
    
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Hours of logs to analyze (default: 24)"
    )
    
    parser.add_argument(
        "--start",
        type=str,
        help="Start time (ISO format: 2025-12-17T00:00:00)"
    )
    
    parser.add_argument(
        "--end",
        type=str,
        help="End time (ISO format: 2025-12-17T23:59:59)"
    )
    
    parser.add_argument(
        "--service",
        type=str,
        help="Filter by service name (comma-separated)"
    )
    
    parser.add_argument(
        "--severity",
        type=str,
        help="Filter by severity (comma-separated: error,critical)"
    )
    
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip sending email alert"
    )
    
    parser.add_argument(
        "--schedule-time",
        type=str,
        default="02:00",
        help="Time for scheduled runs (HH:MM format, default: 02:00)"
    )
    
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Perform health check and exit"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status"
    )
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    try:
        orchestrator = Orchestrator()
    except Exception as e:
        print(f"Failed to initialize orchestrator: {e}")
        sys.exit(1)
    
    # Health check
    if args.health_check:
        health = orchestrator.health_check()
        print(f"Overall Status: {health['overall_status']}")
        print("\nComponents:")
        for component, status in health['components'].items():
            print(f"  {component}: {status['status']}")
            if 'error' in status:
                print(f"    Error: {status['error']}")
        sys.exit(0 if health['overall_status'] == 'healthy' else 1)
    
    # Status
    if args.status:
        print("Agentic AI Log Analysis System")
        print("Status: Running")
        print(f"Mode: {args.mode}")
        sys.exit(0)
    
    # Parse filters
    service_filter = args.service.split(",") if args.service else None
    severity_filter = args.severity.split(",") if args.severity else None
    
    # Run based on mode
    if args.mode == "scheduled":
        print(f"Starting scheduled mode (daily at {args.schedule_time})")
        print("Press Ctrl+C to stop")
        orchestrator.schedule_daily_analysis(
            run_time=args.schedule_time,
            hours=args.hours
        )
    
    else:  # manual mode
        print("Running manual analysis...")
        
        try:
            result = orchestrator.run_analysis(
                start_time=args.start,
                end_time=args.end,
                hours=args.hours if not args.start else None,
                service_filter=service_filter,
                severity_filter=severity_filter,
                send_email=not args.no_email
            )
            
            print(f"\nAnalysis completed: {result['status']}")
            print(f"Execution ID: {result['execution_id']}")
            
            if result.get("stages"):
                print("\nStages:")
                for stage, info in result["stages"].items():
                    print(f"  {stage}: {info.get('status', 'unknown')}")
            
            sys.exit(0 if result['status'] == 'completed_success' else 1)
        
        except Exception as e:
            print(f"\nAnalysis failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
