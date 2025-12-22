"""
Solution Generator Agent

This agent uses AI to generate actionable remediation solutions
based on root cause analysis, including immediate actions and preventive measures.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from utils.logger import get_logger
from utils.helpers import load_yaml_config
from utils.exceptions import SolutionGeneratorException, AIProviderException

logger = get_logger(__name__)


class SolutionGeneratorAgent:
    """
    Agent responsible for generating remediation solutions
    
    Features:
    - AI-powered solution generation
    - Step-by-step remediation plans
    - Preventive measures
    - Risk assessment
    - Confidence scoring
    - Verification steps
    """
    
    def __init__(self, config_path: str = "config/ai.yaml"):
        """
        Initialize Solution Generator Agent
        
        Args:
            config_path: Path to AI configuration file
        """
        self.config = load_yaml_config(config_path)
        self.ai_client = None
        self._initialize_ai_client()
        
        logger.info("Solution Generator Agent initialized")
    
    def _initialize_ai_client(self):
        """Initialize AI client (Google Gemini)"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config["api_key"])
            self.ai_client = genai
            logger.info("AI client initialized", extra={"provider": self.config["provider"]})
        except Exception as e:
            logger.warning(f"Failed to initialize AI client: {e}")
            self.ai_client = None
    
    def generate_solutions(
        self,
        rca_result: Dict[str, Any],
        error_groups: List[Dict[str, Any]],
        statistics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate remediation solutions based on RCA
        
        Args:
            rca_result: Root cause analysis result
            error_groups: Error groups from parser
            statistics: Error statistics
        
        Returns:
            Dictionary containing solutions with confidence scores
        
        Raises:
            SolutionGeneratorException: If solution generation fails
        """
        try:
            logger.info("Generating remediation solutions")
            
            root_causes = rca_result.get("root_causes", [])
            
            if not root_causes:
                logger.warning("No root causes provided, generating generic solutions")
                return self._generate_generic_solutions(error_groups)
            
            solutions = []
            
            # Generate solution for each root cause
            for i, root_cause in enumerate(root_causes[:3], 1):  # Top 3 root causes
                if self.ai_client:
                    solution = self._ai_generate_solution(root_cause, error_groups, rca_result)
                else:
                    solution = self._rule_based_solution(root_cause, error_groups)
                
                if solution:
                    solution["priority"] = i
                    solutions.append(solution)
            
            # Add general best practices
            best_practices = self._generate_best_practices(error_groups, statistics)
            
            result = {
                "solutions": solutions,
                "best_practices": best_practices,
                "overall_confidence": self._calculate_overall_confidence(solutions),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(
                "Solution generation completed",
                extra={
                    "solutions_generated": len(solutions),
                    "confidence": result["overall_confidence"]
                }
            )
            
            return result
        
        except Exception as e:
            logger.error("Solution generation failed", exc_info=True)
            raise SolutionGeneratorException(
                "Failed to generate solutions",
                {"error": str(e)}
            )
    
    def _ai_generate_solution(
        self,
        root_cause: Dict[str, Any],
        error_groups: List[Dict[str, Any]],
        rca_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Use AI to generate solution"""
        
        try:
            # Prepare context
            context = self._prepare_solution_context(root_cause, error_groups, rca_result)
            
            # Get solution generation prompt
            system_prompt = self.config["prompts"]["solution_generation"]["system"]
            
            # Combine system prompt and user context
            full_prompt = f"{system_prompt}\n\n{context}"
            
            # Call Gemini API
            model = self.ai_client.GenerativeModel(self.config["model"])
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": self.config.get("temperature", 0.3),
                    "max_output_tokens": self.config.get("max_tokens", 2000),
                    "top_p": self.config.get("top_p", 1.0),
                    "top_k": self.config.get("top_k", 40),
                }
            )
            
            # Parse response
            ai_response = response.text
            
            try:
                parsed_solution = json.loads(ai_response)
                
                # Add metadata
                parsed_solution["root_cause"] = root_cause["description"]
                parsed_solution["source"] = "ai_generated"
                
                return parsed_solution
            
            except json.JSONDecodeError:
                # Fallback: structure the text response
                return {
                    "root_cause": root_cause["description"],
                    "immediate_actions": [ai_response],
                    "preventive_measures": [],
                    "estimated_time": "Unknown",
                    "confidence": 60,
                    "risks": [],
                    "verification_steps": [],
                    "source": "ai_text_response"
                }
        
        except Exception as e:
            logger.warning(f"AI solution generation failed: {e}")
            return self._rule_based_solution(root_cause, error_groups)
    
    def _prepare_solution_context(
        self,
        root_cause: Dict[str, Any],
        error_groups: List[Dict[str, Any]],
        rca_result: Dict[str, Any]
    ) -> str:
        """Prepare context for AI solution generation"""
        
        context_parts = [
            "# Root Cause Analysis Summary\n\n",
            f"## Root Cause:\n{root_cause['description']}\n\n",
            f"Confidence: {root_cause['confidence']}%\n\n"
        ]
        
        if root_cause.get("affected_services"):
            context_parts.append(
                f"Affected Services: {', '.join(root_cause['affected_services'])}\n\n"
            )
        
        if root_cause.get("contributing_factors"):
            context_parts.append("Contributing Factors:\n")
            for factor in root_cause["contributing_factors"]:
                context_parts.append(f"- {factor}\n")
            context_parts.append("\n")
        
        # Add error group context
        context_parts.append("## Error Details:\n")
        for group in error_groups[:5]:
            context_parts.append(
                f"- {group['service_name']}: {group['error_type']} "
                f"({group['count']} occurrences, severity: {group['severity']})\n"
            )
        
        context_parts.append(
            "\n## Task:\n"
            "Generate a detailed remediation solution in the specified JSON format. "
            "Include immediate actions, preventive measures, estimated time, risks, and verification steps."
        )
        
        return "".join(context_parts)
    
    def _rule_based_solution(
        self,
        root_cause: Dict[str, Any],
        error_groups: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate solution using rule-based approach"""
        
        description = root_cause["description"].lower()
        category = root_cause.get("contributing_factors", [""])[0] if root_cause.get("contributing_factors") else ""
        
        # Database/Connection issues
        if any(keyword in description for keyword in ["database", "connection", "timeout"]):
            return {
                "root_cause": root_cause["description"],
                "immediate_actions": [
                    "Check database server status and connectivity",
                    "Review database connection pool settings",
                    "Verify network connectivity between application and database",
                    "Check for database locks or long-running queries",
                    "Restart database connection pool if necessary"
                ],
                "preventive_measures": [
                    "Implement connection pool monitoring and alerting",
                    "Set appropriate connection timeout values",
                    "Configure automatic connection retry with exponential backoff",
                    "Implement circuit breaker pattern for database calls",
                    "Regular database performance tuning and optimization"
                ],
                "estimated_time": "30-60 minutes",
                "confidence": 75,
                "risks": [
                    "Restarting connection pool may cause brief service interruption",
                    "Database changes may require application restart"
                ],
                "verification_steps": [
                    "Verify database connection pool metrics return to normal",
                    "Check application logs for successful database connections",
                    "Monitor error rates for 15-30 minutes",
                    "Run health check endpoints"
                ],
                "source": "rule_based"
            }
        
        # Authentication/Security issues
        elif any(keyword in description for keyword in ["auth", "security", "permission", "unauthorized"]):
            return {
                "root_cause": root_cause["description"],
                "immediate_actions": [
                    "Verify authentication service is running and accessible",
                    "Check API keys and credentials are valid and not expired",
                    "Review recent security policy changes",
                    "Verify user permissions and roles are correctly configured",
                    "Check for token expiration issues"
                ],
                "preventive_measures": [
                    "Implement automated credential rotation",
                    "Set up monitoring for authentication failures",
                    "Configure proper token expiration and refresh mechanisms",
                    "Regular security audits and access reviews",
                    "Implement rate limiting for authentication attempts"
                ],
                "estimated_time": "20-40 minutes",
                "confidence": 70,
                "risks": [
                    "Credential changes may affect multiple services",
                    "Security policy changes require careful testing"
                ],
                "verification_steps": [
                    "Test authentication flow end-to-end",
                    "Verify users can successfully authenticate",
                    "Check authentication service logs",
                    "Monitor authentication success rates"
                ],
                "source": "rule_based"
            }
        
        # Performance/Resource issues
        elif any(keyword in description for keyword in ["performance", "timeout", "slow", "latency", "resource"]):
            return {
                "root_cause": root_cause["description"],
                "immediate_actions": [
                    "Check system resource utilization (CPU, memory, disk)",
                    "Identify and kill any runaway processes",
                    "Review recent deployments or configuration changes",
                    "Check for memory leaks or resource exhaustion",
                    "Scale up resources if necessary"
                ],
                "preventive_measures": [
                    "Implement auto-scaling based on resource metrics",
                    "Set up resource utilization alerts",
                    "Regular performance testing and optimization",
                    "Implement caching where appropriate",
                    "Code profiling and optimization for slow operations"
                ],
                "estimated_time": "45-90 minutes",
                "confidence": 65,
                "risks": [
                    "Scaling operations may cause brief interruptions",
                    "Resource changes may require application restart"
                ],
                "verification_steps": [
                    "Monitor resource utilization metrics",
                    "Check application response times",
                    "Verify no resource alerts are firing",
                    "Run load tests to confirm performance"
                ],
                "source": "rule_based"
            }
        
        # Generic solution
        else:
            return {
                "root_cause": root_cause["description"],
                "immediate_actions": [
                    "Review recent changes and deployments",
                    "Check service health and status",
                    "Review application and infrastructure logs",
                    "Verify all dependencies are operational",
                    "Restart affected services if necessary"
                ],
                "preventive_measures": [
                    "Implement comprehensive monitoring and alerting",
                    "Set up automated health checks",
                    "Regular system maintenance and updates",
                    "Improve error handling and logging",
                    "Document incident response procedures"
                ],
                "estimated_time": "30-60 minutes",
                "confidence": 50,
                "risks": [
                    "Service restarts may cause brief downtime",
                    "Changes may have unintended side effects"
                ],
                "verification_steps": [
                    "Monitor error rates and logs",
                    "Verify service health checks pass",
                    "Check all dependent services",
                    "Run smoke tests"
                ],
                "source": "rule_based_generic"
            }
    
    def _generate_generic_solutions(self, error_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate generic solutions when no root cause is available"""
        
        solutions = [{
            "root_cause": "Multiple errors detected without clear root cause",
            "immediate_actions": [
                "Review all error logs for common patterns",
                "Check system health across all services",
                "Verify recent deployments and changes",
                "Check for infrastructure issues",
                "Review monitoring dashboards"
            ],
            "preventive_measures": [
                "Improve logging and monitoring coverage",
                "Implement better error tracking",
                "Regular system health checks",
                "Automated testing improvements"
            ],
            "estimated_time": "60-120 minutes",
            "confidence": 40,
            "risks": ["Investigation may take longer without clear root cause"],
            "verification_steps": [
                "Monitor error rates",
                "Check all services are healthy",
                "Review logs for improvements"
            ],
            "source": "generic",
            "priority": 1
        }]
        
        return {
            "solutions": solutions,
            "best_practices": [],
            "overall_confidence": 40,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _generate_best_practices(
        self,
        error_groups: List[Dict[str, Any]],
        statistics: Dict[str, Any]
    ) -> List[str]:
        """Generate general best practices based on error patterns"""
        
        practices = []
        
        # Check for high error counts
        total_errors = sum(group["count"] for group in error_groups)
        if total_errors > 100:
            practices.append(
                "Implement rate limiting and circuit breakers to prevent error cascades"
            )
        
        # Check for multiple services affected
        unique_services = len(set(group["service_name"] for group in error_groups))
        if unique_services > 3:
            practices.append(
                "Review service dependencies and implement better isolation between services"
            )
        
        # Check for critical errors
        critical_errors = [g for g in error_groups if g.get("severity") == "CRITICAL"]
        if critical_errors:
            practices.append(
                "Set up dedicated alerting for critical errors with immediate escalation"
            )
        
        # General practices
        practices.extend([
            "Implement comprehensive logging with correlation IDs for request tracing",
            "Regular review and update of monitoring and alerting thresholds",
            "Conduct post-incident reviews to improve system resilience",
            "Maintain up-to-date runbooks for common failure scenarios"
        ])
        
        return practices
    
    def _calculate_overall_confidence(self, solutions: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score"""
        if not solutions:
            return 0.0
        
        # Use weighted average, giving more weight to higher priority solutions
        total_weight = 0
        weighted_sum = 0
        
        for solution in solutions:
            priority = solution.get("priority", 1)
            confidence = solution.get("confidence", 50)
            weight = 1.0 / priority  # Higher priority = higher weight
            
            weighted_sum += confidence * weight
            total_weight += weight
        
        return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0


# CLI for testing
if __name__ == "__main__":
    import sys
    
    if "--test" in sys.argv:
        print("Testing Solution Generator Agent...")
        
        # Sample test data
        test_rca = {
            "root_causes": [
                {
                    "description": "Database connection timeout",
                    "confidence": 85,
                    "contributing_factors": ["INFRASTRUCTURE"],
                    "affected_services": ["api-gateway", "user-service"]
                }
            ]
        }
        
        test_error_groups = [
            {
                "service_name": "api-gateway",
                "error_type": "ConnectionTimeout",
                "category": "INFRASTRUCTURE",
                "count": 50,
                "severity": "CRITICAL"
            }
        ]
        
        agent = SolutionGeneratorAgent()
        result = agent.generate_solutions(test_rca, test_error_groups, {})
        
        print(f"Generated {len(result['solutions'])} solutions")
        print(f"Overall confidence: {result['overall_confidence']}")
        
        for i, solution in enumerate(result['solutions'], 1):
            print(f"\nSolution {i}:")
            print(f"  Root Cause: {solution['root_cause']}")
            print(f"  Confidence: {solution['confidence']}%")
            print(f"  Immediate Actions: {len(solution['immediate_actions'])}")
            print(f"  Preventive Measures: {len(solution['preventive_measures'])}")
