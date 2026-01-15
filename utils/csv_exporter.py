"""
CSV Exporter Utility

This module provides functionality to export error logs to CSV format
with comprehensive ECS metadata for analysis and reporting.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

from utils.logger import get_logger
from utils.helpers import ensure_directory, sanitize_filename

logger = get_logger(__name__)


class CSVExporter:
    """
    CSV Exporter for error logs
    
    Features:
    - Export logs to CSV with ECS metadata
    - Timestamped filenames
    - Field sanitization
    - Missing field handling
    """
    
    # CSV column headers
    HEADERS = [
        "Timestamp",
        "ECS Cluster Name",
        "ECS Service / Task Name",
        "Log Level",
        "Error Message",
        "Stack Trace",
        "Container Name",
        "Environment"
    ]
    
    def __init__(self, output_dir: str = "results"):
        """
        Initialize CSV Exporter
        
        Args:
            output_dir: Directory to save CSV files
        """
        self.output_dir = ensure_directory(output_dir)
        logger.info(f"CSV Exporter initialized with output directory: {self.output_dir}")
    
    def export_to_csv(
        self,
        logs: List[Dict[str, Any]],
        execution_id: Optional[str] = None
    ) -> Path:
        """
        Export error logs to CSV file
        
        Args:
            logs: List of error log dictionaries
            execution_id: Optional execution ID for filename
        
        Returns:
            Path to generated CSV file
        
        Raises:
            Exception: If CSV generation fails
        """
        try:
            # Generate filename
            if not execution_id:
                execution_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            filename = f"errors_{execution_id}.csv"
            filepath = self.output_dir / filename
            
            logger.info(f"Exporting {len(logs)} error logs to CSV: {filepath}")
            
            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.HEADERS)
                writer.writeheader()
                
                for log in logs:
                    row = self._extract_csv_row(log)
                    writer.writerow(row)
            
            logger.info(f"CSV export completed: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}", exc_info=True)
            raise
    
    def _extract_csv_row(self, log: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract CSV row from log entry
        
        Args:
            log: Log dictionary
        
        Returns:
            Dictionary mapping headers to values
        """
        # Extract timestamp
        timestamp = log.get("timestamp", log.get("@timestamp", ""))
        if timestamp:
            # Ensure ISO format
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except:
                pass  # Keep original if parsing fails
        
        # Extract ECS cluster name
        # Check various possible field names for ECS cluster
        cluster_name = (
            log.get("ecs.cluster.name") or
            log.get("cloud.instance.id") or
            log.get("container.labels.com.amazonaws.ecs.cluster") or
            log.get("cluster_name") or
            ""
        )
        
        # Extract ECS service/task name
        service_name = (
            log.get("ecs.task.family") or
            log.get("service.name") or
            log.get("service_name") or
            log.get("container.labels.com.amazonaws.ecs.task-definition-family") or
            ""
        )
        
        # Extract log level
        log_level = (
            log.get("log.level") or
            log.get("log_level") or
            log.get("level") or
            log.get("severity") or
            ""
        ).upper()
        
        # Extract error message
        error_message = (
            log.get("error.message") or
            log.get("error_message") or
            log.get("message") or
            log.get("log") or
            ""
        )
        
        # Extract stack trace
        stack_trace = (
            log.get("error.stack_trace") or
            log.get("stack_trace") or
            log.get("error.stack") or
            log.get("exception.stacktrace") or
            ""
        )
        
        # Extract container name
        container_name = (
            log.get("container.name") or
            log.get("container_name") or
            log.get("docker.container.name") or
            log.get("container.id") or
            ""
        )
        
        # Extract environment
        environment = (
            log.get("environment") or
            log.get("env") or
            log.get("deployment.environment") or
            log.get("tags.environment") or
            log.get("labels.environment") or
            ""
        )
        
        # Sanitize all fields
        return {
            "Timestamp": self._sanitize_field(timestamp),
            "ECS Cluster Name": self._sanitize_field(cluster_name),
            "ECS Service / Task Name": self._sanitize_field(service_name),
            "Log Level": self._sanitize_field(log_level),
            "Error Message": self._sanitize_field(error_message),
            "Stack Trace": self._sanitize_field(stack_trace),
            "Container Name": self._sanitize_field(container_name),
            "Environment": self._sanitize_field(environment)
        }
    
    def _sanitize_field(self, value: Any) -> str:
        """
        Sanitize CSV field to prevent injection and ensure proper formatting
        
        Args:
            value: Field value
        
        Returns:
            Sanitized string
        """
        if value is None:
            return ""
        
        # Convert to string
        value_str = str(value)
        
        # Remove null bytes
        value_str = value_str.replace('\x00', '')
        
        # Prevent CSV injection by escaping leading special characters
        # that could be interpreted as formulas (=, +, -, @)
        if value_str and value_str[0] in ['=', '+', '-', '@']:
            value_str = "'" + value_str
        
        # Replace newlines with spaces for single-line CSV cells
        # (except for stack traces which we want to preserve)
        if "Stack Trace" not in str(value):
            value_str = value_str.replace('\n', ' ').replace('\r', ' ')
        
        # Truncate very long fields (max 10000 chars)
        if len(value_str) > 10000:
            value_str = value_str[:9997] + "..."
        
        return value_str


def generate_csv_filename(prefix: str = "errors") -> str:
    """
    Generate timestamped CSV filename
    
    Args:
        prefix: Filename prefix
    
    Returns:
        Timestamped filename
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.csv"


def sanitize_csv_field(value: str) -> str:
    """
    Sanitize CSV field value
    
    Args:
        value: Field value to sanitize
    
    Returns:
        Sanitized value
    """
    exporter = CSVExporter()
    return exporter._sanitize_field(value)


# CLI for testing
if __name__ == "__main__":
    import sys
    
    if "--test" in sys.argv:
        print("Testing CSV Exporter...")
        
        # Sample test logs
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
        
        exporter = CSVExporter()
        filepath = exporter.export_to_csv(test_logs, "test")
        
        print(f"✅ CSV file created: {filepath}")
        print(f"✅ Exported {len(test_logs)} logs")
        
        # Read and display
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            print("\nCSV Content Preview:")
            print(content[:500])
