"""
Custom Exception Classes for Agentic Log Analysis System

This module defines all custom exceptions used throughout the system
for precise error handling and reporting.
"""


class AgenticLogAnalysisException(Exception):
    """Base exception for all custom exceptions in the system"""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to dictionary for structured logging"""
        return {
            "exception_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


# Elasticsearch Related Exceptions
class ElasticsearchException(AgenticLogAnalysisException):
    """Base exception for Elasticsearch-related errors"""
    pass


class ElasticsearchConnectionError(ElasticsearchException):
    """Raised when connection to Elasticsearch fails"""
    pass


class ElasticsearchQueryError(ElasticsearchException):
    """Raised when Elasticsearch query execution fails"""
    pass


class ElasticsearchAuthenticationError(ElasticsearchException):
    """Raised when Elasticsearch authentication fails"""
    pass


class ElasticsearchIndexNotFoundError(ElasticsearchException):
    """Raised when specified index does not exist"""
    pass


# Agent Related Exceptions
class AgentException(AgenticLogAnalysisException):
    """Base exception for agent-related errors"""
    pass


class LogFetcherException(AgentException):
    """Raised when Log Fetcher Agent encounters an error"""
    pass


class ErrorParserException(AgentException):
    """Raised when Error Parser Agent encounters an error"""
    pass


class RCAAnalyzerException(AgentException):
    """Raised when RCA Analyzer Agent encounters an error"""
    pass


class SolutionGeneratorException(AgentException):
    """Raised when Solution Generator Agent encounters an error"""
    pass


class EmailSenderException(AgentException):
    """Raised when Email Sender Agent encounters an error"""
    pass


# AI Provider Exceptions
class AIProviderException(AgenticLogAnalysisException):
    """Base exception for AI provider errors"""
    pass


class AIAuthenticationError(AIProviderException):
    """Raised when AI provider authentication fails"""
    pass


class AIRateLimitError(AIProviderException):
    """Raised when AI provider rate limit is exceeded"""
    pass


class AIResponseError(AIProviderException):
    """Raised when AI provider returns invalid response"""
    pass


class AITimeoutError(AIProviderException):
    """Raised when AI provider request times out"""
    pass


# Configuration Exceptions
class ConfigurationException(AgenticLogAnalysisException):
    """Base exception for configuration errors"""
    pass


class ConfigurationFileNotFoundError(ConfigurationException):
    """Raised when configuration file is not found"""
    pass


class ConfigurationValidationError(ConfigurationException):
    """Raised when configuration validation fails"""
    pass


class MissingEnvironmentVariableError(ConfigurationException):
    """Raised when required environment variable is missing"""
    pass


# Email Exceptions
class EmailException(AgenticLogAnalysisException):
    """Base exception for email-related errors"""
    pass


class SMTPConnectionError(EmailException):
    """Raised when SMTP connection fails"""
    pass


class SMTPAuthenticationError(EmailException):
    """Raised when SMTP authentication fails"""
    pass


class EmailSendError(EmailException):
    """Raised when email sending fails"""
    pass


# Data Processing Exceptions
class DataProcessingException(AgenticLogAnalysisException):
    """Base exception for data processing errors"""
    pass


class LogNormalizationError(DataProcessingException):
    """Raised when log normalization fails"""
    pass


class ClassificationError(DataProcessingException):
    """Raised when error classification fails"""
    pass


class AnalysisError(DataProcessingException):
    """Raised when analysis operation fails"""
    pass


# Orchestration Exceptions
class OrchestrationException(AgenticLogAnalysisException):
    """Base exception for orchestration errors"""
    pass


class AgentExecutionError(OrchestrationException):
    """Raised when agent execution fails"""
    pass


class WorkflowError(OrchestrationException):
    """Raised when workflow execution fails"""
    pass


# Validation Exceptions
class ValidationException(AgenticLogAnalysisException):
    """Base exception for validation errors"""
    pass


class InvalidInputError(ValidationException):
    """Raised when input validation fails"""
    pass


class InvalidTimeRangeError(ValidationException):
    """Raised when time range is invalid"""
    pass


class InvalidConfigurationError(ValidationException):
    """Raised when configuration is invalid"""
    pass
