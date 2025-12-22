"""
Error Parser Agent

This agent classifies logs, detects patterns and anomalies,
and groups related errors for analysis.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
from datetime import datetime
import re

from utils.logger import get_logger
from utils.exceptions import ErrorParserException, ClassificationError

logger = get_logger(__name__)


class ErrorParserAgent:
    """
    Agent responsible for parsing and classifying errors
    
    Features:
    - Error classification (Application, Infrastructure, Security, Performance)
    - Pattern detection
    - Error grouping
    - Severity assessment
    - Metadata extraction
    """
    
    # Classification patterns
    CLASSIFICATION_PATTERNS = {
        "APPLICATION": [
            r"exception",
            r"nullpointerexception",
            r"indexoutofbounds",
            r"illegalargument",
            r"runtime error",
            r"syntax error",
            r"type error",
            r"value error",
            r"attribute error",
            r"import error",
            r"assertion error"
        ],
        "INFRASTRUCTURE": [
            r"connection refused",
            r"connection timeout",
            r"network unreachable",
            r"host not found",
            r"dns resolution failed",
            r"disk full",
            r"out of memory",
            r"resource exhausted",
            r"service unavailable",
            r"database connection",
            r"redis connection",
            r"kafka connection"
        ],
        "SECURITY": [
            r"authentication failed",
            r"authorization denied",
            r"access denied",
            r"permission denied",
            r"invalid token",
            r"expired token",
            r"unauthorized",
            r"forbidden",
            r"csrf",
            r"xss",
            r"sql injection",
            r"invalid credentials"
        ],
        "PERFORMANCE": [
            r"timeout",
            r"slow query",
            r"high latency",
            r"response time exceeded",
            r"thread pool exhausted",
            r"queue full",
            r"rate limit exceeded",
            r"throttling",
            r"circuit breaker"
        ]
    }
    
    def __init__(self):
        """Initialize Error Parser Agent"""
        self.compiled_patterns = self._compile_patterns()
        logger.info("Error Parser Agent initialized")
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficiency"""
        compiled = {}
        for category, patterns in self.CLASSIFICATION_PATTERNS.items():
            compiled[category] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled
    
    def parse_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse and classify a batch of logs
        
        Args:
            logs: List of normalized log dictionaries
        
        Returns:
            Dictionary containing classified errors, patterns, and statistics
        
        Raises:
            ErrorParserException: If parsing fails
        """
        try:
            logger.info(f"Parsing {len(logs)} logs")
            
            classified_logs = []
            
            for log in logs:
                classified = self.classify_log(log)
                classified_logs.append(classified)
            
            # Group errors
            error_groups = self.group_errors(classified_logs)
            
            # Detect patterns
            patterns = self.detect_patterns(classified_logs)
            
            # Calculate statistics
            stats = self._calculate_statistics(classified_logs, error_groups)
            
            result = {
                "classified_logs": classified_logs,
                "error_groups": error_groups,
                "patterns": patterns,
                "statistics": stats,
                "total_logs": len(logs),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(
                "Log parsing completed",
                extra={
                    "total_logs": len(logs),
                    "error_groups": len(error_groups),
                    "patterns_detected": len(patterns)
                }
            )
            
            return result
        
        except Exception as e:
            logger.error("Failed to parse logs", exc_info=True)
            raise ErrorParserException(
                "Log parsing failed",
                {"error": str(e), "log_count": len(logs)}
            )
    
    def classify_log(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a single log entry
        
        Args:
            log: Normalized log dictionary
        
        Returns:
            Log with classification metadata
        """
        message = log.get("message", "")
        error_message = log.get("error_message", "")
        error_type = log.get("error_type", "")
        
        # Combine all text for classification
        combined_text = f"{message} {error_message} {error_type}".lower()
        
        # Classify by pattern matching
        category = self._classify_by_patterns(combined_text)
        
        # Assess severity
        severity = self._assess_severity(log, category)
        
        # Extract key information
        extracted_info = self._extract_key_info(log)
        
        # Add classification metadata
        classified = log.copy()
        classified.update({
            "category": category,
            "severity": severity,
            "extracted_info": extracted_info,
            "classified_at": datetime.utcnow().isoformat() + "Z"
        })
        
        return classified
    
    def _classify_by_patterns(self, text: str) -> str:
        """Classify text using pattern matching"""
        
        category_scores = defaultdict(int)
        
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    category_scores[category] += 1
        
        if not category_scores:
            return "UNKNOWN"
        
        # Return category with highest score
        return max(category_scores.items(), key=lambda x: x[1])[0]
    
    def _assess_severity(self, log: Dict[str, Any], category: str) -> str:
        """
        Assess error severity
        
        Returns: CRITICAL, HIGH, MEDIUM, or LOW
        """
        log_level = (log.get("log_level") or "").lower()
        message = (log.get("message", "") + " " + log.get("error_message", "")).lower()
        
        # Critical indicators
        critical_keywords = [
            "critical", "fatal", "disaster", "emergency",
            "data loss", "corruption", "security breach"
        ]
        
        if log_level in ["critical", "fatal"] or any(kw in message for kw in critical_keywords):
            return "CRITICAL"
        
        # High severity indicators
        high_keywords = [
            "error", "failed", "failure", "exception",
            "unavailable", "down", "crash"
        ]
        
        if log_level == "error" or any(kw in message for kw in high_keywords):
            # Security and infrastructure errors are typically high severity
            if category in ["SECURITY", "INFRASTRUCTURE"]:
                return "HIGH"
            return "MEDIUM"
        
        # Default to medium for warnings, low for others
        if log_level == "warning":
            return "MEDIUM"
        
        return "LOW"
    
    def _extract_key_info(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information from log"""
        
        message = log.get("message", "")
        
        # Extract error codes (e.g., E001, ERR-123, HTTP 500)
        error_codes = re.findall(r'\b(?:E\d+|ERR-\d+|HTTP\s+\d{3})\b', message, re.IGNORECASE)
        
        # Extract IPs
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', message)
        
        # Extract URLs
        urls = re.findall(r'https?://[^\s]+', message)
        
        # Extract file paths
        file_paths = re.findall(r'(?:/[\w.-]+)+|(?:[A-Z]:\\[\w\\.-]+)', message)
        
        return {
            "error_codes": error_codes,
            "ip_addresses": ips,
            "urls": urls,
            "file_paths": file_paths
        }
    
    def group_errors(self, classified_logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group related errors together
        
        Args:
            classified_logs: List of classified logs
        
        Returns:
            List of error groups with metadata
        """
        groups = defaultdict(list)
        
        for log in classified_logs:
            # Group by category, service, and error type
            key = (
                log.get("category", "UNKNOWN"),
                log.get("service_name", "unknown"),
                log.get("error_type", "unknown")
            )
            groups[key].append(log)
        
        error_groups = []
        
        for (category, service, error_type), logs in groups.items():
            group = {
                "category": category,
                "service_name": service,
                "error_type": error_type,
                "count": len(logs),
                "severity": self._group_severity(logs),
                "first_occurrence": min(log.get("timestamp", "") for log in logs),
                "last_occurrence": max(log.get("timestamp", "") for log in logs),
                "sample_logs": logs[:5],  # Keep first 5 as samples
                "affected_hosts": list(set(log.get("host_name") for log in logs if log.get("host_name")))
            }
            error_groups.append(group)
        
        # Sort by count (most frequent first)
        error_groups.sort(key=lambda x: x["count"], reverse=True)
        
        return error_groups
    
    def _group_severity(self, logs: List[Dict[str, Any]]) -> str:
        """Determine group severity based on individual log severities"""
        severities = [log.get("severity", "LOW") for log in logs]
        
        if "CRITICAL" in severities:
            return "CRITICAL"
        elif "HIGH" in severities:
            return "HIGH"
        elif "MEDIUM" in severities:
            return "MEDIUM"
        else:
            return "LOW"
    
    def detect_patterns(self, classified_logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect patterns and anomalies in logs
        
        Args:
            classified_logs: List of classified logs
        
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Pattern 1: Spike in errors from specific service
        service_counts = Counter(log.get("service_name") for log in classified_logs)
        for service, count in service_counts.most_common(5):
            if count > 10:  # Threshold for spike
                patterns.append({
                    "type": "ERROR_SPIKE",
                    "service": service,
                    "count": count,
                    "description": f"High error count from service: {service}"
                })
        
        # Pattern 2: Cascading failures (same error across multiple services)
        error_type_counts = Counter(log.get("error_type") for log in classified_logs)
        for error_type, count in error_type_counts.most_common(3):
            if error_type and count > 5:
                affected_services = set(
                    log.get("service_name")
                    for log in classified_logs
                    if log.get("error_type") == error_type
                )
                if len(affected_services) > 2:
                    patterns.append({
                        "type": "CASCADING_FAILURE",
                        "error_type": error_type,
                        "affected_services": list(affected_services),
                        "count": count,
                        "description": f"Same error across multiple services: {error_type}"
                    })
        
        # Pattern 3: Temporal clustering (many errors in short time)
        if len(classified_logs) > 20:
            timestamps = [log.get("timestamp") for log in classified_logs if log.get("timestamp")]
            if timestamps:
                patterns.append({
                    "type": "TEMPORAL_CLUSTERING",
                    "count": len(classified_logs),
                    "time_range": f"{min(timestamps)} to {max(timestamps)}",
                    "description": "High concentration of errors in short time period"
                })
        
        return patterns
    
    def _calculate_statistics(
        self,
        classified_logs: List[Dict[str, Any]],
        error_groups: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate statistics for the analysis"""
        
        category_counts = Counter(log.get("category") for log in classified_logs)
        severity_counts = Counter(log.get("severity") for log in classified_logs)
        service_counts = Counter(log.get("service_name") for log in classified_logs)
        
        return {
            "by_category": dict(category_counts),
            "by_severity": dict(severity_counts),
            "by_service": dict(service_counts.most_common(10)),
            "total_error_groups": len(error_groups),
            "unique_services": len(service_counts),
            "unique_error_types": len(set(log.get("error_type") for log in classified_logs))
        }


# CLI for testing
if __name__ == "__main__":
    import sys
    
    if "--test" in sys.argv:
        print("Testing Error Parser Agent...")
        
        # Sample test logs
        test_logs = [
            {
                "timestamp": "2025-12-17T20:00:00Z",
                "message": "NullPointerException in UserService",
                "log_level": "error",
                "service_name": "user-service",
                "error_type": "NullPointerException"
            },
            {
                "timestamp": "2025-12-17T20:01:00Z",
                "message": "Connection timeout to database",
                "log_level": "error",
                "service_name": "api-gateway",
                "error_type": "ConnectionTimeout"
            },
            {
                "timestamp": "2025-12-17T20:02:00Z",
                "message": "Authentication failed for user",
                "log_level": "warning",
                "service_name": "auth-service",
                "error_type": "AuthenticationError"
            }
        ]
        
        agent = ErrorParserAgent()
        result = agent.parse_logs(test_logs)
        
        print(f"Classified {result['total_logs']} logs")
        print(f"Found {len(result['error_groups'])} error groups")
        print(f"Detected {len(result['patterns'])} patterns")
        print(f"Statistics: {result['statistics']}")
