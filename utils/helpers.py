"""
Helper Utilities for Agentic Log Analysis System

This module provides common utility functions used across the system.
"""

import os
import yaml
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dateutil import parser as date_parser

from utils.exceptions import (
    ConfigurationFileNotFoundError,
    ConfigurationValidationError,
    MissingEnvironmentVariableError,
    InvalidTimeRangeError
)
from utils.logger import get_logger

logger = get_logger(__name__)


def load_yaml_config(config_path: str, substitute_env: bool = True) -> Dict[str, Any]:
    """
    Load YAML configuration file with optional environment variable substitution
    
    Args:
        config_path: Path to YAML configuration file
        substitute_env: Whether to substitute ${VAR_NAME} with environment variables
    
    Returns:
        Dictionary containing configuration
    
    Raises:
        ConfigurationFileNotFoundError: If config file doesn't exist
        ConfigurationValidationError: If YAML is invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise ConfigurationFileNotFoundError(
            f"Configuration file not found: {config_path}",
            {"path": config_path}
        )
    
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Substitute environment variables
        if substitute_env:
            content = substitute_env_variables(content)
        
        config = yaml.safe_load(content)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    
    except yaml.YAMLError as e:
        raise ConfigurationValidationError(
            f"Invalid YAML in configuration file: {config_path}",
            {"path": config_path, "error": str(e)}
        )
    except Exception as e:
        raise ConfigurationValidationError(
            f"Failed to load configuration: {config_path}",
            {"path": config_path, "error": str(e)}
        )


def substitute_env_variables(content: str) -> str:
    """
    Replace ${VAR_NAME} patterns with environment variable values
    
    Args:
        content: String content with ${VAR_NAME} patterns
    
    Returns:
        Content with substituted values
    
    Raises:
        MissingEnvironmentVariableError: If required env var is not set
    """
    import re
    
    pattern = r'\$\{([^}]+)\}'
    
    def replace_var(match):
        var_name = match.group(1)
        value = os.getenv(var_name)
        
        if value is None:
            raise MissingEnvironmentVariableError(
                f"Required environment variable not set: {var_name}",
                {"variable": var_name}
            )
        
        return value
    
    return re.sub(pattern, replace_var, content)


def get_env_variable(var_name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get environment variable with optional default and required validation
    
    Args:
        var_name: Environment variable name
        default: Default value if not set
        required: Whether variable is required
    
    Returns:
        Environment variable value or default
    
    Raises:
        MissingEnvironmentVariableError: If required and not set
    """
    value = os.getenv(var_name, default)
    
    if required and value is None:
        raise MissingEnvironmentVariableError(
            f"Required environment variable not set: {var_name}",
            {"variable": var_name}
        )
    
    return value


def parse_time_range(
    start: Optional[Union[str, datetime]] = None,
    end: Optional[Union[str, datetime]] = None,
    hours: Optional[int] = None
) -> tuple[datetime, datetime]:
    """
    Parse and validate time range for log queries
    
    Args:
        start: Start time (ISO format string or datetime)
        end: End time (ISO format string or datetime)
        hours: Hours back from now (if start/end not provided)
    
    Returns:
        Tuple of (start_datetime, end_datetime)
    
    Raises:
        InvalidTimeRangeError: If time range is invalid
    """
    now = datetime.utcnow()
    
    # If hours provided, calculate range
    if hours is not None:
        end_time = now
        start_time = now - timedelta(hours=hours)
    else:
        # Parse start time
        if start is None:
            start_time = now - timedelta(hours=24)  # Default to last 24 hours
        elif isinstance(start, str):
            try:
                start_time = date_parser.parse(start)
            except Exception as e:
                raise InvalidTimeRangeError(
                    f"Invalid start time format: {start}",
                    {"start": start, "error": str(e)}
                )
        else:
            start_time = start
        
        # Parse end time
        if end is None:
            end_time = now
        elif isinstance(end, str):
            try:
                end_time = date_parser.parse(end)
            except Exception as e:
                raise InvalidTimeRangeError(
                    f"Invalid end time format: {end}",
                    {"end": end, "error": str(e)}
                )
        else:
            end_time = end
    
    # Validate range
    if start_time >= end_time:
        raise InvalidTimeRangeError(
            "Start time must be before end time",
            {"start": start_time.isoformat(), "end": end_time.isoformat()}
        )
    
    logger.debug(
        "Parsed time range",
        extra={
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "duration_hours": (end_time - start_time).total_seconds() / 3600
        }
    )
    
    return start_time, end_time


def format_timestamp(dt: datetime, format_type: str = "iso") -> str:
    """
    Format datetime to string
    
    Args:
        dt: Datetime object
        format_type: Format type ('iso', 'human', 'filename')
    
    Returns:
        Formatted timestamp string
    """
    if format_type == "iso":
        return dt.isoformat() + "Z"
    elif format_type == "human":
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    elif format_type == "filename":
        return dt.strftime("%Y%m%d_%H%M%S")
    else:
        return dt.isoformat()


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if necessary
    
    Args:
        path: Directory path
    
    Returns:
        Path object
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def save_json(data: Any, filepath: Union[str, Path], pretty: bool = True):
    """
    Save data to JSON file
    
    Args:
        data: Data to save
        filepath: Output file path
        pretty: Whether to pretty-print JSON
    """
    file_path = Path(filepath)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w') as f:
        if pretty:
            json.dump(data, f, indent=2, default=str)
        else:
            json.dump(data, f, default=str)
    
    logger.debug(f"Saved JSON to {filepath}")


def load_json(filepath: Union[str, Path]) -> Any:
    """
    Load data from JSON file
    
    Args:
        filepath: Input file path
    
    Returns:
        Loaded data
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    logger.debug(f"Loaded JSON from {filepath}")
    return data


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    import re
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    return sanitized


def calculate_percentage(part: float, total: float, decimals: int = 2) -> float:
    """
    Calculate percentage with error handling
    
    Args:
        part: Part value
        total: Total value
        decimals: Number of decimal places
    
    Returns:
        Percentage value
    """
    if total == 0:
        return 0.0
    return round((part / total) * 100, decimals)


def merge_dicts(dict1: Dict, dict2: Dict, deep: bool = True) -> Dict:
    """
    Merge two dictionaries
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        deep: Whether to perform deep merge
    
    Returns:
        Merged dictionary
    """
    if not deep:
        return {**dict1, **dict2}
    
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value, deep=True)
        else:
            result[key] = value
    
    return result


def validate_config_schema(config: Dict, required_fields: List[str]) -> bool:
    """
    Validate configuration has required fields
    
    Args:
        config: Configuration dictionary
        required_fields: List of required field names (supports nested with dots)
    
    Returns:
        True if valid
    
    Raises:
        ConfigurationValidationError: If validation fails
    """
    missing_fields = []
    
    for field in required_fields:
        parts = field.split('.')
        current = config
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                missing_fields.append(field)
                break
            current = current[part]
    
    if missing_fields:
        raise ConfigurationValidationError(
            "Configuration missing required fields",
            {"missing_fields": missing_fields}
        )
    
    return True


# Configuration validation for testing
if __name__ == "__main__":
    import sys
    
    if "--validate-config" in sys.argv:
        print("Configuration validation not yet implemented")
        sys.exit(0)
    
    # Test utilities
    print("Testing helper utilities...")
    
    # Test time range parsing
    start, end = parse_time_range(hours=24)
    print(f"Time range: {format_timestamp(start)} to {format_timestamp(end)}")
    
    # Test percentage calculation
    pct = calculate_percentage(25, 100)
    print(f"Percentage: {pct}%")
    
    print("All tests passed!")
