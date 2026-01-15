"""
CloudWatch Log Fetcher Agent

This agent fetches logs from AWS CloudWatch Logs for ECS tasks,
Lambda functions, and other AWS services.
"""

import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from utils.logger import get_logger
from utils.helpers import load_yaml_config, format_timestamp
from utils.exceptions import LogFetcherException

logger = get_logger(__name__)


class CloudWatchFetcherAgent:
    """
    Agent responsible for fetching logs from AWS CloudWatch

    Features:
    - ECS task log fetching
    - Time-based filtering
    - Error pattern filtering
    - Log normalization to match Elasticsearch format
    """

    def __init__(self, profile_name: str = None, region: str = 'us-east-1'):
        """
        Initialize CloudWatch Fetcher Agent

        Args:
            profile_name: AWS profile name (None for default)
            region: AWS region
        """
        self.profile_name = profile_name
        self.region = region
        self.session = None
        self.logs_client = None
        self.ecs_client = None

        self._initialize_clients()
        logger.info("CloudWatch Fetcher Agent initialized",
                   extra={"profile": profile_name, "region": region})

    def _initialize_clients(self):
        """Initialize AWS clients"""
        try:
            self.session = boto3.Session(
                profile_name=self.profile_name,
                region_name=self.region
            )
            self.logs_client = self.session.client('logs')
            self.ecs_client = self.session.client('ecs')
            logger.info("AWS clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise LogFetcherException(
                "Failed to initialize AWS clients",
                {"error": str(e)}
            )

    def get_ecs_log_config(self, cluster: str, task_id: str) -> Dict[str, str]:
        """
        Get log configuration for an ECS task

        Args:
            cluster: ECS cluster name or ARN
            task_id: ECS task ID

        Returns:
            Dict with log_group, log_region, stream_prefix, container_name
        """
        try:
            # Describe the task
            response = self.ecs_client.describe_tasks(
                cluster=cluster,
                tasks=[task_id]
            )

            if not response['tasks']:
                raise LogFetcherException(
                    "ECS task not found",
                    {"cluster": cluster, "task_id": task_id}
                )

            task = response['tasks'][0]
            task_def_arn = task.get('taskDefinitionArn')

            # Get task definition
            td_response = self.ecs_client.describe_task_definition(
                taskDefinition=task_def_arn
            )
            task_def = td_response['taskDefinition']

            # Get first container's log config
            for container in task_def.get('containerDefinitions', []):
                log_config = container.get('logConfiguration', {})
                if log_config.get('logDriver') == 'awslogs':
                    options = log_config.get('options', {})
                    return {
                        'log_group': options.get('awslogs-group'),
                        'log_region': options.get('awslogs-region', self.region),
                        'stream_prefix': options.get('awslogs-stream-prefix', 'ecs'),
                        'container_name': container.get('name'),
                        'task_id': task_id
                    }

            raise LogFetcherException(
                "No awslogs configuration found in task definition",
                {"task_definition": task_def_arn}
            )

        except Exception as e:
            logger.error(f"Failed to get ECS log config: {e}")
            raise

    def fetch_logs(
        self,
        log_group: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        hours: Optional[int] = None,
        stream_prefix: Optional[str] = None,
        filter_pattern: Optional[str] = None,
        max_logs: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Fetch logs from CloudWatch

        Args:
            log_group: CloudWatch log group name
            start_time: Start of time range
            end_time: End of time range
            hours: Hours back from now (alternative to start/end)
            stream_prefix: Log stream prefix filter
            filter_pattern: CloudWatch filter pattern
            max_logs: Maximum number of logs to retrieve

        Returns:
            List of normalized log dictionaries
        """
        # Calculate time range
        if hours:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
        elif not start_time:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
        elif not end_time:
            end_time = datetime.utcnow()

        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)

        logger.info(
            "Fetching CloudWatch logs",
            extra={
                "log_group": log_group,
                "start_time": format_timestamp(start_time),
                "end_time": format_timestamp(end_time),
                "max_logs": max_logs
            }
        )

        try:
            all_logs = []
            kwargs = {
                'logGroupName': log_group,
                'startTime': start_ms,
                'endTime': end_ms,
                'limit': min(max_logs, 10000)
            }

            if stream_prefix:
                kwargs['logStreamNamePrefix'] = stream_prefix

            if filter_pattern:
                kwargs['filterPattern'] = filter_pattern

            # Paginate through results
            while len(all_logs) < max_logs:
                response = self.logs_client.filter_log_events(**kwargs)
                events = response.get('events', [])

                for event in events:
                    if len(all_logs) >= max_logs:
                        break
                    all_logs.append(self._normalize_log(event, log_group))

                # Check for more pages
                next_token = response.get('nextToken')
                if not next_token or not events:
                    break
                kwargs['nextToken'] = next_token

            logger.info(f"Successfully fetched {len(all_logs)} logs from CloudWatch")
            return all_logs

        except Exception as e:
            logger.error(f"Failed to fetch CloudWatch logs: {e}")
            raise LogFetcherException(
                "Failed to fetch CloudWatch logs",
                {"log_group": log_group, "error": str(e)}
            )

    def fetch_ecs_logs(
        self,
        cluster: str,
        task_id: str,
        hours: int = 24,
        filter_pattern: Optional[str] = None,
        max_logs: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Fetch logs for a specific ECS task

        Args:
            cluster: ECS cluster name
            task_id: ECS task ID
            hours: Hours of logs to fetch
            filter_pattern: CloudWatch filter pattern
            max_logs: Maximum logs to retrieve

        Returns:
            List of normalized log dictionaries
        """
        # Get log configuration from ECS
        log_config = self.get_ecs_log_config(cluster, task_id)

        stream_prefix = f"{log_config['stream_prefix']}/{log_config['container_name']}/{task_id}"

        return self.fetch_logs(
            log_group=log_config['log_group'],
            hours=hours,
            stream_prefix=stream_prefix,
            filter_pattern=filter_pattern,
            max_logs=max_logs
        )

    def fetch_error_logs(
        self,
        log_group: str,
        hours: int = 24,
        stream_prefix: Optional[str] = None,
        max_logs: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Fetch only error-level logs

        Args:
            log_group: CloudWatch log group name
            hours: Hours of logs to fetch
            stream_prefix: Log stream prefix
            max_logs: Maximum logs to retrieve

        Returns:
            List of error logs
        """
        error_pattern = '?ERROR ?Exception ?FATAL ?CRITICAL ?error ?exception ?failed ?failure'

        return self.fetch_logs(
            log_group=log_group,
            hours=hours,
            stream_prefix=stream_prefix,
            filter_pattern=error_pattern,
            max_logs=max_logs
        )

    def _normalize_log(self, event: Dict, log_group: str) -> Dict[str, Any]:
        """
        Normalize CloudWatch log event to internal format
        (Compatible with Elasticsearch format for downstream agents)

        Args:
            event: CloudWatch log event
            log_group: Log group name

        Returns:
            Normalized log dictionary
        """
        message = event.get('message', '')
        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)

        # Parse log level from message
        log_level = self._extract_log_level(message)

        # Parse service name from log group or stream
        service_name = self._extract_service_name(
            log_group,
            event.get('logStreamName', '')
        )

        # Extract error info if present
        error_type, error_message = self._extract_error_info(message)

        normalized = {
            "timestamp": timestamp.isoformat() + "Z",
            "message": message,
            "log_level": log_level,
            "service_name": service_name,
            "host_name": event.get('logStreamName', ''),
            "error_message": error_message,
            "error_stack_trace": self._extract_stack_trace(message),
            "error_type": error_type,
            "event_dataset": "cloudwatch",
            "event_module": "aws",
            "raw": {
                "@timestamp": timestamp.isoformat() + "Z",
                "message": message,
                "log": {"level": log_level},
                "service": {"name": service_name},
                "error": {
                    "type": error_type,
                    "message": error_message
                },
                "cloudwatch": {
                    "log_group": log_group,
                    "log_stream": event.get('logStreamName'),
                    "event_id": event.get('eventId')
                }
            }
        }

        return normalized

    def _extract_log_level(self, message: str) -> str:
        """Extract log level from message"""
        message_lower = message.lower()

        if 'fatal' in message_lower or 'critical' in message_lower:
            return 'critical'
        elif 'error' in message_lower:
            return 'error'
        elif 'warn' in message_lower:
            return 'warning'
        elif 'debug' in message_lower:
            return 'debug'
        elif 'trace' in message_lower:
            return 'trace'
        else:
            return 'info'

    def _extract_service_name(self, log_group: str, log_stream: str) -> str:
        """Extract service name from log group/stream"""
        # Try to extract from log group (e.g., /ecs/myapp -> myapp)
        if log_group.startswith('/ecs/'):
            return log_group.split('/')[-1]
        elif log_group.startswith('/aws/lambda/'):
            return log_group.split('/')[-1]

        # Try to extract from stream (e.g., ecs/container/task-id)
        if '/' in log_stream:
            parts = log_stream.split('/')
            if len(parts) >= 2:
                return parts[1]

        return log_group.split('/')[-1] or 'unknown'

    def _extract_error_info(self, message: str) -> tuple:
        """Extract error type and message"""
        import re

        # Common Java exception patterns
        exception_match = re.search(
            r'(\w+(?:Exception|Error|Failure))\s*[:\-]?\s*(.{0,200})',
            message
        )

        if exception_match:
            return exception_match.group(1), exception_match.group(2).strip()

        # Check for generic error messages
        if 'error' in message.lower():
            return 'Error', message[:200]

        return None, None

    def _extract_stack_trace(self, message: str) -> Optional[str]:
        """Extract stack trace if present"""
        if '\tat ' in message or 'Traceback' in message:
            return message
        return None

    def test_connection(self) -> bool:
        """Test AWS CloudWatch connection"""
        try:
            self.logs_client.describe_log_groups(limit=1)
            return True
        except Exception as e:
            logger.error(f"CloudWatch connection test failed: {e}")
            return False


# CLI for testing
if __name__ == "__main__":
    import sys

    if "--test" in sys.argv:
        print("Testing CloudWatch Fetcher Agent...")

        agent = CloudWatchFetcherAgent(profile_name='ca-prod')

        if agent.test_connection():
            print("Connection successful!")

            # Test fetching ECS logs
            logs = agent.fetch_ecs_logs(
                cluster='CA-PROD-CLR',
                task_id='2e19b1275e554c7dab9adb43077cd490',
                hours=1,
                max_logs=10
            )

            print(f"Fetched {len(logs)} logs")
            if logs:
                print(f"Sample log: {logs[0]}")
        else:
            print("Connection failed!")

        sys.exit(0)
