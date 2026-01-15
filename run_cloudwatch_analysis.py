#!/usr/bin/env python3
"""
CloudWatch Log Analysis Script

Run the complete analysis pipeline using CloudWatch logs instead of Elasticsearch.
"""

import os
import sys
import argparse
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


def run_cloudwatch_analysis(
    log_group: str = None,
    cluster: str = None,
    task_id: str = None,
    hours: int = 24,
    profile: str = None,
    region: str = 'us-east-1',
    send_email: bool = True,
    errors_only: bool = True
):
    """
    Run analysis on CloudWatch logs

    Args:
        log_group: CloudWatch log group (if not using ECS task)
        cluster: ECS cluster name
        task_id: ECS task ID
        hours: Hours of logs to analyze
        profile: AWS profile name
        region: AWS region
        send_email: Whether to send email alert
        errors_only: Only fetch error-level logs
    """
    execution_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    print(f"🚀 Starting CloudWatch Log Analysis")
    print(f"   Execution ID: {execution_id}")
    print(f"   Time Range: Last {hours} hours")
    print("=" * 60)

    result = {
        "execution_id": execution_id,
        "start_time": datetime.utcnow().isoformat() + "Z",
        "source": "cloudwatch",
        "status": "in_progress",
        "stages": {}
    }

    try:
        # Stage 1: Fetch CloudWatch Logs
        print("\n📥 Stage 1: Fetching CloudWatch logs...")

        profile = profile or os.getenv('AWS_PROFILE', 'ca-prod')
        region = region or os.getenv('AWS_REGION', 'us-east-1')

        cw_fetcher = CloudWatchFetcherAgent(profile_name=profile, region=region)

        if cluster and task_id:
            print(f"   Fetching logs for ECS task: {task_id}")
            if errors_only:
                logs = cw_fetcher.fetch_error_logs(
                    log_group=cw_fetcher.get_ecs_log_config(cluster, task_id)['log_group'],
                    hours=hours,
                    stream_prefix=f"ecs/{cw_fetcher.get_ecs_log_config(cluster, task_id)['container_name']}/{task_id}"
                )
            else:
                logs = cw_fetcher.fetch_ecs_logs(
                    cluster=cluster,
                    task_id=task_id,
                    hours=hours
                )
        else:
            log_group = log_group or os.getenv('CLOUDWATCH_LOG_GROUP', '/ecs/myapp')
            print(f"   Fetching logs from: {log_group}")

            if errors_only:
                logs = cw_fetcher.fetch_error_logs(
                    log_group=log_group,
                    hours=hours
                )
            else:
                logs = cw_fetcher.fetch_logs(
                    log_group=log_group,
                    hours=hours
                )

        result["stages"]["log_fetching"] = {
            "status": "success",
            "logs_count": len(logs)
        }

        print(f"   ✅ Fetched {len(logs)} logs")

        if not logs:
            print("\n✅ No error logs found! Application appears healthy.")
            result["status"] = "completed_no_errors"
            result["end_time"] = datetime.utcnow().isoformat() + "Z"
            return result

        # Stage 2: Parse and Classify Errors
        print("\n🔍 Stage 2: Parsing and classifying errors...")

        error_parser = ErrorParserAgent()
        parse_result = error_parser.parse_logs(logs)

        result["stages"]["error_parsing"] = {
            "status": "success",
            "error_groups": len(parse_result["error_groups"]),
            "patterns": len(parse_result["patterns"])
        }

        print(f"   ✅ Found {len(parse_result['error_groups'])} error groups")
        print(f"   ✅ Detected {len(parse_result['patterns'])} patterns")

        # Export to CSV
        csv_exporter = CSVExporter()
        csv_filepath = csv_exporter.export_to_csv(logs, execution_id)
        result["csv_file"] = str(csv_filepath)
        print(f"   ✅ Exported to: {csv_filepath}")

        # Stage 3: Root Cause Analysis
        print("\n🧠 Stage 3: Performing AI-powered root cause analysis...")

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

        print(f"   ✅ Identified {len(rca_result['root_causes'])} root causes")
        print(f"   ✅ Confidence: {rca_result['confidence_score']}%")

        # Stage 4: Generate Solutions
        print("\n💡 Stage 4: Generating remediation solutions...")

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

        print(f"   ✅ Generated {len(solutions['solutions'])} solutions")

        # Stage 5: Send Email Alert
        if send_email and parse_result["error_groups"]:
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

            print(f"   ✅ Email {'sent successfully' if email_sent else 'failed'}")

        # Save results
        results_dir = ensure_directory("results")
        results_file = results_dir / f"cloudwatch_analysis_{execution_id}.json"
        save_json({
            "metadata": result,
            "logs_sample": logs[:10],
            "parse_result": parse_result,
            "rca_result": rca_result,
            "solutions": solutions
        }, results_file)

        result["status"] = "completed_success"
        result["end_time"] = datetime.utcnow().isoformat() + "Z"

        print("\n" + "=" * 60)
        print("✅ Analysis completed successfully!")
        print(f"   Results saved to: {results_file}")

        # Print summary
        print("\n📊 Summary:")
        print(f"   Total logs analyzed: {len(logs)}")
        print(f"   Error groups: {len(parse_result['error_groups'])}")
        print(f"   Root causes: {len(rca_result['root_causes'])}")
        print(f"   Solutions: {len(solutions['solutions'])}")

        if rca_result['root_causes']:
            print("\n🔍 Top Root Causes:")
            for i, rc in enumerate(rca_result['root_causes'][:3], 1):
                print(f"   {i}. {rc['description'][:80]}... (confidence: {rc['confidence']}%)")

        return result

    except Exception as e:
        print(f"\n❌ Error: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
        result["end_time"] = datetime.utcnow().isoformat() + "Z"
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Run log analysis on CloudWatch logs"
    )

    parser.add_argument(
        "--log-group",
        type=str,
        help="CloudWatch log group name"
    )

    parser.add_argument(
        "--cluster",
        type=str,
        help="ECS cluster name"
    )

    parser.add_argument(
        "--task-id",
        type=str,
        help="ECS task ID"
    )

    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Hours of logs to analyze (default: 24)"
    )

    parser.add_argument(
        "--profile",
        type=str,
        help="AWS profile name"
    )

    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )

    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip sending email alert"
    )

    parser.add_argument(
        "--all-logs",
        action="store_true",
        help="Fetch all logs, not just errors"
    )

    args = parser.parse_args()

    try:
        run_cloudwatch_analysis(
            log_group=args.log_group,
            cluster=args.cluster,
            task_id=args.task_id,
            hours=args.hours,
            profile=args.profile,
            region=args.region,
            send_email=not args.no_email,
            errors_only=not args.all_logs
        )
    except Exception as e:
        print(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
