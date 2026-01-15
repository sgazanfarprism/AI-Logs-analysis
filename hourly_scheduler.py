#!/usr/bin/env python3
"""
Hourly Log Analysis Scheduler

Runs CloudWatch log analysis every hour and sends email alerts
with CSV attachments and AI-powered RCA solutions.
"""

import os
import sys
import time
import signal
import schedule
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents.cloudwatch_fetcher_agent import CloudWatchFetcherAgent
from agents.error_parser_agent import ErrorParserAgent
from agents.rca_analyzer_agent import RCAAnalyzerAgent
from agents.solution_gen_agent import SolutionGeneratorAgent
from agents.email_sender_agent import EmailSenderAgent
from utils.helpers import save_json, ensure_directory, format_timestamp, parse_time_range
from utils.csv_exporter import CSVExporter
from utils.logger import get_logger

logger = get_logger(__name__)

# Global flag for graceful shutdown
running = True


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    logger.info("Received shutdown signal, stopping scheduler...")
    running = False


def run_hourly_analysis():
    """
    Run the complete hourly log analysis pipeline
    """
    execution_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    logger.info(f"Starting hourly analysis - Execution ID: {execution_id}")
    print(f"\n{'='*60}")
    print(f"🕐 Hourly Analysis Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   Execution ID: {execution_id}")
    print(f"{'='*60}")

    result = {
        "execution_id": execution_id,
        "start_time": datetime.utcnow().isoformat() + "Z",
        "source": "cloudwatch",
        "schedule": "hourly",
        "status": "in_progress",
        "stages": {}
    }

    try:
        # Configuration
        profile = os.getenv('AWS_PROFILE', 'ca-prod')
        region = os.getenv('AWS_REGION', 'us-east-1')
        log_group = os.getenv('CLOUDWATCH_LOG_GROUP', '/ecs/myapp')
        hours = 1  # Last 1 hour

        # Stage 1: Fetch CloudWatch Logs
        print("\n📥 Stage 1: Fetching last 1 hour of logs...")

        cw_fetcher = CloudWatchFetcherAgent(profile_name=profile, region=region)

        # Fetch all logs from last hour (not just errors, to have complete picture)
        all_logs = cw_fetcher.fetch_logs(
            log_group=log_group,
            hours=hours,
            max_logs=50000
        )

        # Also fetch error-specific logs
        error_logs = cw_fetcher.fetch_error_logs(
            log_group=log_group,
            hours=hours,
            max_logs=10000
        )

        result["stages"]["log_fetching"] = {
            "status": "success",
            "total_logs": len(all_logs),
            "error_logs": len(error_logs)
        }

        print(f"   ✅ Total logs: {len(all_logs)}")
        print(f"   ✅ Error logs: {len(error_logs)}")

        # Export ALL logs to CSV (for attachment)
        csv_exporter = CSVExporter()
        csv_filepath = csv_exporter.export_to_csv(all_logs, f"hourly_{execution_id}")
        result["csv_file"] = str(csv_filepath)
        print(f"   ✅ Exported to: {csv_filepath}")

        # If no error logs, still send a health report
        if not error_logs:
            print("\n✅ No errors found in the last hour!")
            logger.info("No errors found in hourly analysis")

            # Send health check email
            _send_health_email(execution_id, len(all_logs), csv_filepath)

            result["status"] = "completed_healthy"
            result["end_time"] = datetime.utcnow().isoformat() + "Z"
            result["message"] = "No errors detected - system healthy"

            _save_results(execution_id, result, None, None, None)
            return result

        # Stage 2: Parse and Classify Errors
        print("\n🔍 Stage 2: Parsing and classifying errors...")

        error_parser = ErrorParserAgent()
        parse_result = error_parser.parse_logs(error_logs)

        result["stages"]["error_parsing"] = {
            "status": "success",
            "error_groups": len(parse_result["error_groups"]),
            "patterns": len(parse_result["patterns"])
        }

        print(f"   ✅ Error groups: {len(parse_result['error_groups'])}")
        print(f"   ✅ Patterns detected: {len(parse_result['patterns'])}")

        # Stage 3: AI-Powered Root Cause Analysis
        print("\n🧠 Stage 3: AI-Powered Root Cause Analysis...")

        rca_analyzer = RCAAnalyzerAgent()
        rca_result = rca_analyzer.analyze(
            parse_result["error_groups"],
            parse_result["patterns"],
            parse_result["statistics"]
        )

        result["stages"]["rca_analysis"] = {
            "status": "success",
            "root_causes": len(rca_result["root_causes"]),
            "confidence": rca_result["confidence_score"]
        }

        print(f"   ✅ Root causes identified: {len(rca_result['root_causes'])}")
        print(f"   ✅ Confidence: {rca_result['confidence_score']}%")

        # Stage 4: AI-Powered Solution Generation
        print("\n💡 Stage 4: Generating AI Solutions...")

        solution_gen = SolutionGeneratorAgent()
        solutions = solution_gen.generate_solutions(
            rca_result,
            parse_result["error_groups"],
            parse_result["statistics"]
        )

        result["stages"]["solution_generation"] = {
            "status": "success",
            "solutions": len(solutions["solutions"]),
            "confidence": solutions["overall_confidence"]
        }

        print(f"   ✅ Solutions generated: {len(solutions['solutions'])}")

        # Stage 5: Send Email Alert
        print("\n📧 Stage 5: Sending email alert...")

        start_dt, end_dt = parse_time_range(hours=hours)
        time_range = f"{format_timestamp(start_dt, 'human')} to {format_timestamp(end_dt, 'human')}"

        email_sender = EmailSenderAgent()
        email_sent = email_sender.send_alert(
            result,
            parse_result["error_groups"],
            rca_result,
            solutions,
            parse_result["statistics"],
            time_range,
            csv_filepath
        )

        result["stages"]["email_sending"] = {
            "status": "success" if email_sent else "failed"
        }

        print(f"   ✅ Email {'sent successfully' if email_sent else 'FAILED'}")

        # Save results
        _save_results(execution_id, result, parse_result, rca_result, solutions)

        result["status"] = "completed_with_errors"
        result["end_time"] = datetime.utcnow().isoformat() + "Z"

        print(f"\n{'='*60}")
        print(f"✅ Hourly analysis completed!")
        print(f"   Errors found: {len(error_logs)}")
        print(f"   Root causes: {len(rca_result['root_causes'])}")
        print(f"   Solutions: {len(solutions['solutions'])}")
        print(f"{'='*60}\n")

        return result

    except Exception as e:
        logger.error(f"Hourly analysis failed: {e}", exc_info=True)
        print(f"\n❌ Analysis failed: {e}")

        result["status"] = "failed"
        result["error"] = str(e)
        result["end_time"] = datetime.utcnow().isoformat() + "Z"

        # Try to send failure notification
        try:
            _send_failure_email(execution_id, str(e))
        except:
            pass

        return result


def _send_health_email(execution_id: str, log_count: int, csv_filepath: str):
    """Send a health check email when no errors are found"""
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.application import MIMEApplication
        import smtplib
        from pathlib import Path

        recipients = os.getenv('ALERT_RECIPIENTS', '').split(',')

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: #4caf50; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .footer {{ color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✅ Hourly Health Check - All Clear</h1>
            </div>
            <div class="content">
                <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Execution ID:</strong> {execution_id}</p>
                <p><strong>Status:</strong> <span style="color: green;">HEALTHY</span></p>
                <p><strong>Total Logs Analyzed:</strong> {log_count}</p>
                <p><strong>Errors Found:</strong> 0</p>
                <hr>
                <p>No errors or warnings were detected in the last hour. The application is running normally.</p>
                <p>The complete log file for the last hour is attached for reference.</p>
            </div>
            <div class="footer">
                <p>This is an automated hourly health check from the Agentic Log Analysis System.</p>
                <p>Regards,<br>Syed Gazanfar</p>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Health Check] ✅ All Clear - {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        msg["From"] = f"Agentic Log Analysis <{os.getenv('SMTP_USERNAME')}>"
        msg["To"] = ", ".join(recipients)

        msg.attach(MIMEText(html_body, "html"))

        # Attach CSV
        if csv_filepath and Path(csv_filepath).exists():
            with open(csv_filepath, 'rb') as f:
                csv_attachment = MIMEApplication(f.read(), _subtype="csv")
                csv_attachment.add_header(
                    'Content-Disposition', 'attachment',
                    filename=Path(csv_filepath).name
                )
                msg.attach(csv_attachment)

        # Send email
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))

        server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
        server.starttls()
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD').strip('"'))
        server.sendmail(os.getenv('SMTP_USERNAME'), recipients, msg.as_string())
        server.quit()

        logger.info("Health check email sent successfully")
        print("   ✅ Health check email sent")

    except Exception as e:
        logger.error(f"Failed to send health email: {e}")
        print(f"   ⚠️ Failed to send health email: {e}")


def _send_failure_email(execution_id: str, error: str):
    """Send notification when analysis fails"""
    try:
        import smtplib
        from email.mime.text import MIMEText

        recipients = os.getenv('ALERT_RECIPIENTS', '').split(',')

        body = f"""
        ⚠️ HOURLY ANALYSIS FAILED

        Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        Execution ID: {execution_id}

        Error: {error}

        Please check the system logs for more details.

        ---
        Agentic Log Analysis System
        """

        msg = MIMEText(body)
        msg["Subject"] = f"[ALERT] Hourly Analysis Failed - {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        msg["From"] = os.getenv('SMTP_USERNAME')
        msg["To"] = ", ".join(recipients)

        server = smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT')), timeout=30)
        server.starttls()
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD').strip('"'))
        server.sendmail(os.getenv('SMTP_USERNAME'), recipients, msg.as_string())
        server.quit()

    except Exception as e:
        logger.error(f"Failed to send failure notification: {e}")


def _save_results(execution_id, result, parse_result, rca_result, solutions):
    """Save analysis results to file"""
    try:
        results_dir = ensure_directory("results")
        results_file = results_dir / f"hourly_analysis_{execution_id}.json"

        data = {
            "metadata": result,
            "parse_result": parse_result,
            "rca_result": rca_result,
            "solutions": solutions
        }

        save_json(data, results_file)
        logger.info(f"Results saved to {results_file}")

    except Exception as e:
        logger.error(f"Failed to save results: {e}")


def main():
    """Main entry point for the hourly scheduler"""
    global running

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("""
╔═══════════════════════════════════════════════════════════════╗
║         AGENTIC LOG ANALYSIS - HOURLY SCHEDULER               ║
║                                                               ║
║  Automated CloudWatch log analysis with AI-powered RCA        ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    print(f"📧 Email Recipients: {os.getenv('ALERT_RECIPIENTS')}")
    print(f"☁️  CloudWatch Log Group: {os.getenv('CLOUDWATCH_LOG_GROUP')}")
    print(f"🌎 AWS Region: {os.getenv('AWS_REGION')}")
    print(f"⏰ Schedule: Every hour at :00")
    print()

    # Run immediately on startup
    print("🚀 Running initial analysis...")
    run_hourly_analysis()

    # Schedule hourly runs at the top of each hour
    schedule.every().hour.at(":00").do(run_hourly_analysis)

    print(f"\n⏰ Scheduler started. Next run at the top of the hour.")
    print("   Press Ctrl+C to stop.\n")

    # Run the scheduler
    while running:
        schedule.run_pending()
        time.sleep(30)  # Check every 30 seconds

    print("\n👋 Scheduler stopped gracefully.")


if __name__ == "__main__":
    main()
