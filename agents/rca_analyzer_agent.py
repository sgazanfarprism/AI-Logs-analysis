"""
RCA (Root Cause Analysis) Analyzer Agent

This agent performs causal reasoning to identify root causes of errors,
correlates events across services, and ranks causes by probability.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

from utils.logger import get_logger
from utils.helpers import load_yaml_config
from utils.exceptions import RCAAnalyzerException, AIProviderException

logger = get_logger(__name__)


class RCAAnalyzerAgent:
    """
    Agent responsible for Root Cause Analysis
    
    Features:
    - Causal reasoning
    - Temporal correlation
    - Service dependency analysis
    - Error propagation tracking
    - AI-powered analysis
    - Confidence scoring
    """
    
    def __init__(self, config_path: str = "config/ai.yaml"):
        """
        Initialize RCA Analyzer Agent
        
        Args:
            config_path: Path to AI configuration file
        """
        self.config = load_yaml_config(config_path)
        self.ai_client = None
        self._initialize_ai_client()
        
        logger.info("RCA Analyzer Agent initialized")
    
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
    
    def analyze(
        self,
        error_groups: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        statistics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform root cause analysis on error groups
        
        Args:
            error_groups: Grouped errors from Error Parser
            patterns: Detected patterns
            statistics: Error statistics
        
        Returns:
            RCA report with root causes and confidence scores
        
        Raises:
            RCAAnalyzerException: If analysis fails
        """
        try:
            logger.info(
                "Starting RCA analysis",
                extra={
                    "error_groups": len(error_groups),
                    "patterns": len(patterns)
                }
            )
            
            # Perform correlation analysis
            correlations = self._correlate_events(error_groups)
            
            # Identify temporal relationships
            temporal_analysis = self._analyze_temporal_relationships(error_groups)
            
            # Analyze service dependencies
            dependency_analysis = self._analyze_service_dependencies(error_groups)
            
            # Perform AI-powered RCA if available
            ai_analysis = None
            if self.ai_client:
                ai_analysis = self._ai_powered_rca(
                    error_groups,
                    patterns,
                    correlations,
                    temporal_analysis
                )
            
            # Combine analyses to determine root causes
            root_causes = self._determine_root_causes(
                error_groups,
                patterns,
                correlations,
                temporal_analysis,
                dependency_analysis,
                ai_analysis
            )
            
            result = {
                "root_causes": root_causes,
                "correlations": correlations,
                "temporal_analysis": temporal_analysis,
                "dependency_analysis": dependency_analysis,
                "ai_analysis": ai_analysis,
                "confidence_score": self._calculate_overall_confidence(root_causes),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(
                "RCA analysis completed",
                extra={
                    "root_causes_found": len(root_causes),
                    "confidence": result["confidence_score"]
                }
            )
            
            return result
        
        except Exception as e:
            logger.error("RCA analysis failed", exc_info=True)
            raise RCAAnalyzerException(
                "Failed to perform root cause analysis",
                {"error": str(e)}
            )
    
    def _correlate_events(self, error_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Correlate events across error groups"""
        
        correlations = []
        
        # Find error groups with overlapping time ranges
        for i, group1 in enumerate(error_groups):
            for group2 in error_groups[i+1:]:
                if self._time_ranges_overlap(group1, group2):
                    correlation = {
                        "group1": {
                            "service": group1["service_name"],
                            "error_type": group1["error_type"],
                            "category": group1["category"]
                        },
                        "group2": {
                            "service": group2["service_name"],
                            "error_type": group2["error_type"],
                            "category": group2["category"]
                        },
                        "correlation_type": "TEMPORAL",
                        "strength": self._calculate_correlation_strength(group1, group2)
                    }
                    correlations.append(correlation)
        
        # Sort by correlation strength
        correlations.sort(key=lambda x: x["strength"], reverse=True)
        
        return correlations[:10]  # Return top 10 correlations
    
    def _time_ranges_overlap(self, group1: Dict, group2: Dict) -> bool:
        """Check if time ranges of two groups overlap"""
        try:
            start1 = datetime.fromisoformat(group1["first_occurrence"].replace("Z", ""))
            end1 = datetime.fromisoformat(group1["last_occurrence"].replace("Z", ""))
            start2 = datetime.fromisoformat(group2["first_occurrence"].replace("Z", ""))
            end2 = datetime.fromisoformat(group2["last_occurrence"].replace("Z", ""))
            
            return start1 <= end2 and start2 <= end1
        except:
            return False
    
    def _calculate_correlation_strength(self, group1: Dict, group2: Dict) -> float:
        """Calculate correlation strength between two error groups (0-1)"""
        
        strength = 0.0
        
        # Same category increases correlation
        if group1["category"] == group2["category"]:
            strength += 0.3
        
        # Infrastructure errors often cause application errors
        if (group1["category"] == "INFRASTRUCTURE" and group2["category"] == "APPLICATION") or \
           (group2["category"] == "INFRASTRUCTURE" and group1["category"] == "APPLICATION"):
            strength += 0.4
        
        # Similar timing increases correlation
        try:
            time1 = datetime.fromisoformat(group1["first_occurrence"].replace("Z", ""))
            time2 = datetime.fromisoformat(group2["first_occurrence"].replace("Z", ""))
            time_diff = abs((time1 - time2).total_seconds())
            
            if time_diff < 60:  # Within 1 minute
                strength += 0.3
            elif time_diff < 300:  # Within 5 minutes
                strength += 0.2
        except:
            pass
        
        return min(strength, 1.0)
    
    def _analyze_temporal_relationships(self, error_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns in errors"""
        
        # Sort groups by first occurrence
        sorted_groups = sorted(
            error_groups,
            key=lambda x: x.get("first_occurrence", "")
        )
        
        # Identify potential cascade
        cascade = []
        if len(sorted_groups) >= 2:
            first_error = sorted_groups[0]
            cascade.append({
                "order": 1,
                "service": first_error["service_name"],
                "error_type": first_error["error_type"],
                "category": first_error["category"],
                "timestamp": first_error["first_occurrence"],
                "likely_root_cause": True
            })
            
            for i, group in enumerate(sorted_groups[1:], start=2):
                cascade.append({
                    "order": i,
                    "service": group["service_name"],
                    "error_type": group["error_type"],
                    "category": group["category"],
                    "timestamp": group["first_occurrence"],
                    "likely_root_cause": False
                })
        
        return {
            "error_cascade": cascade,
            "first_error": sorted_groups[0] if sorted_groups else None,
            "total_duration_seconds": self._calculate_total_duration(sorted_groups)
        }
    
    def _calculate_total_duration(self, sorted_groups: List[Dict[str, Any]]) -> float:
        """Calculate total duration from first to last error"""
        if len(sorted_groups) < 2:
            return 0.0
        
        try:
            first = datetime.fromisoformat(sorted_groups[0]["first_occurrence"].replace("Z", ""))
            last = datetime.fromisoformat(sorted_groups[-1]["last_occurrence"].replace("Z", ""))
            return (last - first).total_seconds()
        except:
            return 0.0
    
    def _analyze_service_dependencies(self, error_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze service dependency relationships"""
        
        services = set(group["service_name"] for group in error_groups)
        
        # Common dependency patterns
        dependency_hints = {
            "api-gateway": ["upstream services"],
            "auth-service": ["database", "cache"],
            "user-service": ["database", "auth-service"],
            "payment-service": ["database", "external-api"]
        }
        
        affected_services = list(services)
        potential_dependencies = []
        
        for service in services:
            if service in dependency_hints:
                potential_dependencies.extend(dependency_hints[service])
        
        return {
            "affected_services": affected_services,
            "potential_upstream_dependencies": list(set(potential_dependencies)),
            "service_count": len(services)
        }
    
    def _ai_powered_rca(
        self,
        error_groups: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        correlations: List[Dict[str, Any]],
        temporal_analysis: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Use AI to perform advanced RCA"""
        
        try:
            # Prepare context for AI
            context = self._prepare_ai_context(
                error_groups,
                patterns,
                correlations,
                temporal_analysis
            )
            
            # Get RCA prompt from config
            system_prompt = self.config["prompts"]["root_cause_analysis"]["system"]
            
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
            
            # Parse AI response
            ai_response = response.text
            
            # Try to parse as JSON
            try:
                parsed_response = json.loads(ai_response)
                return parsed_response
            except json.JSONDecodeError:
                # If not JSON, return as text
                return {
                    "root_cause": ai_response,
                    "confidence": 70,
                    "source": "ai_text_response"
                }
        
        except Exception as e:
            logger.warning(f"AI-powered RCA failed: {e}")
            return None
    
    def _prepare_ai_context(
        self,
        error_groups: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        correlations: List[Dict[str, Any]],
        temporal_analysis: Dict[str, Any]
    ) -> str:
        """Prepare context for AI analysis"""
        
        # Limit context size
        max_groups = self.config.get("max_context_logs", 50)
        
        context_parts = [
            "# Error Analysis Context\n",
            f"\n## Error Groups (Top {min(len(error_groups), 10)}):\n"
        ]
        
        for i, group in enumerate(error_groups[:10], 1):
            context_parts.append(
                f"{i}. Service: {group['service_name']}, "
                f"Category: {group['category']}, "
                f"Error: {group['error_type']}, "
                f"Count: {group['count']}, "
                f"Severity: {group['severity']}\n"
            )
        
        if patterns:
            context_parts.append("\n## Detected Patterns:\n")
            for pattern in patterns:
                context_parts.append(f"- {pattern.get('description', 'Unknown pattern')}\n")
        
        if temporal_analysis.get("error_cascade"):
            context_parts.append("\n## Error Cascade (Temporal Order):\n")
            for item in temporal_analysis["error_cascade"][:5]:
                context_parts.append(
                    f"{item['order']}. {item['service']} - {item['error_type']} "
                    f"at {item['timestamp']}\n"
                )
        
        context_parts.append("\n## Question:\n")
        context_parts.append(
            "Based on the above error data, what is the most probable root cause? "
            "Provide your analysis in the specified JSON format."
        )
        
        return "".join(context_parts)
    
    def _determine_root_causes(
        self,
        error_groups: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        correlations: List[Dict[str, Any]],
        temporal_analysis: Dict[str, Any]],
        dependency_analysis: Dict[str, Any],
        ai_analysis: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Determine root causes by combining all analyses"""
        
        root_causes = []
        
        # If AI analysis available, use it as primary
        if ai_analysis:
            root_causes.append({
                "description": ai_analysis.get("root_cause", "Unknown"),
                "confidence": ai_analysis.get("confidence", 70),
                "source": "ai_analysis",
                "contributing_factors": ai_analysis.get("contributing_factors", []),
                "affected_services": ai_analysis.get("affected_services", []),
                "evidence": "AI-powered analysis"
            })
        
        # Add temporal analysis insights
        if temporal_analysis.get("first_error"):
            first_error = temporal_analysis["first_error"]
            root_causes.append({
                "description": f"Initial failure in {first_error['service_name']}: {first_error['error_type']}",
                "confidence": 75,
                "source": "temporal_analysis",
                "contributing_factors": [first_error['category']],
                "affected_services": [first_error['service_name']],
                "evidence": "First error in temporal sequence"
            })
        
        # Add pattern-based insights
        for pattern in patterns:
            if pattern["type"] == "CASCADING_FAILURE":
                root_causes.append({
                    "description": f"Cascading failure: {pattern.get('error_type', 'Unknown')}",
                    "confidence": 65,
                    "source": "pattern_detection",
                    "contributing_factors": ["service_dependency"],
                    "affected_services": pattern.get("affected_services", []),
                    "evidence": f"Same error across {len(pattern.get('affected_services', []))} services"
                })
        
        # Deduplicate and sort by confidence
        root_causes.sort(key=lambda x: x["confidence"], reverse=True)
        
        return root_causes[:5]  # Return top 5 root causes
    
    def _calculate_overall_confidence(self, root_causes: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score"""
        if not root_causes:
            return 0.0
        
        # Use highest confidence as overall
        return max(rc["confidence"] for rc in root_causes)


# CLI for testing
if __name__ == "__main__":
    import sys
    
    if "--test" in sys.argv:
        print("Testing RCA Analyzer Agent...")
        
        # Sample test data
        test_error_groups = [
            {
                "service_name": "database",
                "error_type": "ConnectionTimeout",
                "category": "INFRASTRUCTURE",
                "count": 50,
                "severity": "CRITICAL",
                "first_occurrence": "2025-12-17T20:00:00Z",
                "last_occurrence": "2025-12-17T20:05:00Z"
            },
            {
                "service_name": "api-gateway",
                "error_type": "ServiceUnavailable",
                "category": "APPLICATION",
                "count": 100,
                "severity": "HIGH",
                "first_occurrence": "2025-12-17T20:01:00Z",
                "last_occurrence": "2025-12-17T20:06:00Z"
            }
        ]
        
        test_patterns = [
            {
                "type": "CASCADING_FAILURE",
                "affected_services": ["database", "api-gateway"],
                "description": "Cascading failure detected"
            }
        ]
        
        agent = RCAAnalyzerAgent()
        result = agent.analyze(test_error_groups, test_patterns, {})
        
        print(f"Found {len(result['root_causes'])} root causes")
        print(f"Overall confidence: {result['confidence_score']}")
        for i, rc in enumerate(result['root_causes'], 1):
            print(f"{i}. {rc['description']} (confidence: {rc['confidence']})")
