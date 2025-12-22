"""
Log Fetcher Agent

This agent is responsible for querying Elasticsearch for ECS-formatted logs,
handling pagination, filtering, and normalizing log data.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import (
    ConnectionError as ESConnectionError,
    AuthenticationException,
    NotFoundError
)
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.logger import get_logger
from utils.helpers import load_yaml_config, parse_time_range, format_timestamp
from utils.exceptions import (
    ElasticsearchConnectionError,
    ElasticsearchAuthenticationError,
    ElasticsearchQueryError,
    ElasticsearchIndexNotFoundError,
    LogFetcherException
)

logger = get_logger(__name__)


class LogFetcherAgent:
    """
    Agent responsible for fetching logs from Elasticsearch
    
    Features:
    - ECS format support
    - Time-based filtering
    - Service and severity filtering
    - Pagination handling
    - Connection retry logic
    - Log normalization
    """
    
    def __init__(self, config_path: str = "config/elasticsearch.yaml"):
        """
        Initialize Log Fetcher Agent
        
        Args:
            config_path: Path to Elasticsearch configuration file
        """
        self.config = load_yaml_config(config_path)
        self.es_client = None
        self.field_mappings = self.config.get("field_mappings", {})
        
        logger.info("Log Fetcher Agent initialized", extra={"config_path": config_path})
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def connect(self):
        """
        Establish connection to Elasticsearch with retry logic
        
        Raises:
            ElasticsearchConnectionError: If connection fails
            ElasticsearchAuthenticationError: If authentication fails
        """
        try:
            host = self.config["host"]
            port = self.config["port"]
            use_ssl = self.config.get("use_ssl", "true").lower() == "true"
            
            es_url = f"{'https' if use_ssl else 'http'}://{host}:{port}"
            
            self.es_client = Elasticsearch(
                [es_url],
                basic_auth=(self.config["username"], self.config["password"]),
                verify_certs=self.config.get("verify_certs", True),
                request_timeout=self.config.get("timeout", 30)
            )
            
            # Test connection
            info = self.es_client.info()
            
            logger.info(
                "Connected to Elasticsearch",
                extra={
                    "cluster_name": info["cluster_name"],
                    "version": info["version"]["number"]
                }
            )
        
        except AuthenticationException as e:
            logger.error("Elasticsearch authentication failed", exc_info=True)
            raise ElasticsearchAuthenticationError(
                "Failed to authenticate with Elasticsearch",
                {"host": host, "error": str(e)}
            )
        
        except ESConnectionError as e:
            logger.error("Elasticsearch connection failed", exc_info=True)
            raise ElasticsearchConnectionError(
                "Failed to connect to Elasticsearch",
                {"host": host, "port": port, "error": str(e)}
            )
        
        except Exception as e:
            logger.error("Unexpected error connecting to Elasticsearch", exc_info=True)
            raise ElasticsearchConnectionError(
                "Unexpected error during Elasticsearch connection",
                {"error": str(e)}
            )
    
    def fetch_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        hours: Optional[int] = None,
        service_filter: Optional[List[str]] = None,
        severity_filter: Optional[List[str]] = None,
        max_logs: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch logs from Elasticsearch with filtering
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            hours: Hours back from now (alternative to start/end)
            service_filter: List of service names to filter
            severity_filter: List of log levels to filter
            max_logs: Maximum number of logs to retrieve
        
        Returns:
            List of normalized log dictionaries
        
        Raises:
            LogFetcherException: If log fetching fails
        """
        if not self.es_client:
            self.connect()
        
        # Parse time range
        start_dt, end_dt = parse_time_range(start_time, end_time, hours)
        
        # Build query
        query = self._build_query(start_dt, end_dt, service_filter, severity_filter)
        
        # Determine max logs
        max_logs = max_logs or self.config.get("max_logs_per_query", 100000)
        
        logger.info(
            "Fetching logs from Elasticsearch",
            extra={
                "start_time": format_timestamp(start_dt),
                "end_time": format_timestamp(end_dt),
                "max_logs": max_logs,
                "service_filter": service_filter,
                "severity_filter": severity_filter
            }
        )
        
        try:
            logs = self._execute_query(query, max_logs)
            
            logger.info(
                "Successfully fetched logs",
                extra={"count": len(logs)}
            )
            
            return logs
        
        except Exception as e:
            logger.error("Failed to fetch logs", exc_info=True)
            raise LogFetcherException(
                "Failed to fetch logs from Elasticsearch",
                {"error": str(e)}
            )
    
    def _build_query(
        self,
        start_time: datetime,
        end_time: datetime,
        service_filter: Optional[List[str]],
        severity_filter: Optional[List[str]]
    ) -> Dict:
        """Build Elasticsearch query"""
        
        must_clauses = [
            {
                "range": {
                    self.field_mappings["timestamp"]: {
                        "gte": format_timestamp(start_time),
                        "lte": format_timestamp(end_time)
                    }
                }
            }
        ]
        
        # Add severity filter
        if severity_filter:
            must_clauses.append({
                "terms": {
                    self.field_mappings["log_level"]: [s.lower() for s in severity_filter]
                }
            })
        else:
            # Use default log levels from config
            default_levels = self.config.get("default_log_levels", ["error", "critical"])
            must_clauses.append({
                "terms": {
                    self.field_mappings["log_level"]: default_levels
                }
            })
        
        # Add service filter
        if service_filter:
            must_clauses.append({
                "terms": {
                    self.field_mappings["service_name"]: service_filter
                }
            })
        
        query = {
            "query": {
                "bool": {
                    "must": must_clauses
                }
            },
            "sort": [
                {self.field_mappings["timestamp"]: {"order": "desc"}}
            ]
        }
        
        return query
    
    def _execute_query(self, query: Dict, max_logs: int) -> List[Dict[str, Any]]:
        """Execute query with pagination"""
        
        index_pattern = self.config["index_pattern"]
        scroll_size = self.config.get("scroll_size", 1000)
        scroll_timeout = self.config.get("scroll_timeout", "5m")
        
        all_logs = []
        
        try:
            # Initial search
            response = self.es_client.search(
                index=index_pattern,
                body=query,
                size=min(scroll_size, max_logs),
                scroll=scroll_timeout
            )
            
            scroll_id = response.get("_scroll_id")
            hits = response["hits"]["hits"]
            
            # Process initial batch
            for hit in hits:
                if len(all_logs) >= max_logs:
                    break
                all_logs.append(self._normalize_log(hit["_source"]))
            
            # Scroll through remaining results
            while scroll_id and len(all_logs) < max_logs:
                response = self.es_client.scroll(
                    scroll_id=scroll_id,
                    scroll=scroll_timeout
                )
                
                hits = response["hits"]["hits"]
                
                if not hits:
                    break
                
                for hit in hits:
                    if len(all_logs) >= max_logs:
                        break
                    all_logs.append(self._normalize_log(hit["_source"]))
                
                scroll_id = response.get("_scroll_id")
            
            # Clear scroll
            if scroll_id:
                self.es_client.clear_scroll(scroll_id=scroll_id)
        
        except NotFoundError as e:
            raise ElasticsearchIndexNotFoundError(
                f"Index not found: {index_pattern}",
                {"index": index_pattern, "error": str(e)}
            )
        
        except Exception as e:
            raise ElasticsearchQueryError(
                "Query execution failed",
                {"error": str(e)}
            )
        
        return all_logs
    
    def _normalize_log(self, raw_log: Dict) -> Dict[str, Any]:
        """
        Normalize ECS log to internal format
        
        Args:
            raw_log: Raw log from Elasticsearch
        
        Returns:
            Normalized log dictionary
        """
        normalized = {
            "timestamp": self._get_field(raw_log, self.field_mappings.get("timestamp")),
            "message": self._get_field(raw_log, self.field_mappings.get("message")),
            "log_level": self._get_field(raw_log, self.field_mappings.get("log_level")),
            "service_name": self._get_field(raw_log, self.field_mappings.get("service_name")),
            "host_name": self._get_field(raw_log, self.field_mappings.get("host_name")),
            "error_message": self._get_field(raw_log, self.field_mappings.get("error_message")),
            "error_stack_trace": self._get_field(raw_log, self.field_mappings.get("error_stack_trace")),
            "error_type": self._get_field(raw_log, self.field_mappings.get("error_type")),
            "event_dataset": self._get_field(raw_log, self.field_mappings.get("event_dataset")),
            "event_module": self._get_field(raw_log, self.field_mappings.get("event_module")),
            "raw": raw_log  # Keep raw log for reference
        }
        
        return normalized
    
    def _get_field(self, log: Dict, field_path: Optional[str]) -> Any:
        """
        Get field value from nested dictionary using dot notation
        
        Args:
            log: Log dictionary
            field_path: Field path (e.g., "error.message")
        
        Returns:
            Field value or None
        """
        if not field_path:
            return None
        
        parts = field_path.split(".")
        current = log
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def test_connection(self) -> bool:
        """
        Test Elasticsearch connection
        
        Returns:
            True if connection successful
        """
        try:
            self.connect()
            return True
        except Exception as e:
            logger.error("Connection test failed", exc_info=True)
            return False


# CLI for testing
if __name__ == "__main__":
    import sys
    
    agent = LogFetcherAgent()
    
    if "--test-connection" in sys.argv:
        print("Testing Elasticsearch connection...")
        if agent.test_connection():
            print("Connection successful!")
        else:
            print("Connection failed!")
        sys.exit(0)
    
    if "--test" in sys.argv:
        print("Testing Log Fetcher Agent...")
        try:
            logs = agent.fetch_logs(hours=1, max_logs=10)
            print(f"Fetched {len(logs)} logs")
            if logs:
                print(f"Sample log: {logs[0]}")
        except Exception as e:
            print(f"Test failed: {e}")
            sys.exit(1)
