"""
Email Sender Agent

This agent sends structured email alerts with error details,
RCA, and solutions via SMTP.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.logger import get_logger
from utils.helpers import load_yaml_config, format_timestamp, truncate_string
from utils.exceptions import (
    EmailSenderException,
    SMTPConnectionError,
    SMTPAuthenticationError,
    EmailSendError
)

logger = get_logger(__name__)


class EmailSenderAgent:
    """
    Agent responsible for sending email alerts
    
    Features:
    - HTML email formatting
    - SMTP with TLS support
    - Retry logic
    - Template-based emails
    - Attachment support (future)
    """
    
    def __init__(self, config_path: str = "config/smtp.yaml"):
        """
        Initialize Email Sender Agent
        
        Args:
            config_path: Path to SMTP configuration file
        """
        self.config = load_yaml_config(config_path)
        logger.info("Email Sender Agent initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def send_alert(
        self,
        analysis_result: Dict[str, Any],
        error_groups: List[Dict[str, Any]],
        rca_result: Dict[str, Any],
        solutions: Dict[str, Any],
        statistics: Dict[str, Any],
        time_range: str
    ) -> bool:
        """
        Send email alert with complete analysis
        
        Args:
            analysis_result: Complete analysis result
            error_groups: Error groups from parser
            rca_result: RCA analysis result
            solutions: Generated solutions
            statistics: Error statistics
            time_range: Time range analyzed
        
        Returns:
            True if email sent successfully
        
        Raises:
            EmailSenderException: If email sending fails
        """
        try:
            logger.info("Preparing email alert")
            
            # Prepare email content
            subject = self._generate_subject(error_groups, statistics, time_range)
            html_body = self._generate_html_body(
                error_groups,
                rca_result,
                solutions,
                statistics,
                time_range
            )
            
            # Get recipients
            recipients = self._parse_recipients()
            
            # Send email
            self._send_email(recipients, subject, html_body)
            
            logger.info(
                "Email alert sent successfully",
                extra={"recipients": len(recipients)}
            )
            
            return True
        
        except Exception as e:
            logger.error("Failed to send email alert", exc_info=True)
            raise EmailSenderException(
                "Failed to send email alert",
                {"error": str(e)}
            )
    
    def _generate_subject(
        self,
        error_groups: List[Dict[str, Any]],
        statistics: Dict[str, Any],
        time_range: str
    ) -> str:
        """Generate email subject"""
        
        total_errors = sum(group["count"] for group in error_groups)
        
        # Determine severity
        severities = [group.get("severity", "LOW") for group in error_groups]
        if "CRITICAL" in severities:
            severity = "CRITICAL"
        elif "HIGH" in severities:
            severity = "HIGH"
        elif "MEDIUM" in severities:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        subject_template = self.config.get(
            "subject_template",
            "[Log Alert] {severity} - {error_count} errors detected in {time_range}"
        )
        
        return subject_template.format(
            severity=severity,
            error_count=total_errors,
            time_range=time_range
        )
    
    def _generate_html_body(
        self,
        error_groups: List[Dict[str, Any]],
        rca_result: Dict[str, Any],
        solutions: Dict[str, Any],
        statistics: Dict[str, Any],
        time_range: str
    ) -> str:
        """Generate HTML email body"""
        
        # Get template
        template = self.config.get("html_template", "")
        
        # Calculate summary data
        total_errors = sum(group["count"] for group in error_groups)
        affected_services = list(set(group["service_name"] for group in error_groups))
        
        # Determine overall severity
        severities = [group.get("severity", "LOW") for group in error_groups]
        if "CRITICAL" in severities:
            severity = "CRITICAL"
            severity_class = "critical"
        elif "HIGH" in severities:
            severity = "HIGH"
            severity_class = "high"
        elif "MEDIUM" in severities:
            severity = "MEDIUM"
            severity_class = "medium"
        else:
            severity = "LOW"
            severity_class = "low"
        
        # Generate error details HTML
        error_details_html = self._format_error_details(error_groups)
        
        # Generate RCA HTML
        rca_html = self._format_rca(rca_result)
        
        # Generate solutions HTML
        solutions_html = self._format_solutions(solutions)
        
        # Fill template
        html = template.format(
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            time_range=time_range,
            error_count=total_errors,
            severity=severity,
            severity_class=severity_class,
            affected_services=", ".join(affected_services[:10]),
            error_details=error_details_html,
            rca_content=rca_html,
            solution_content=solutions_html
        )
        
        return html
    
    def _format_error_details(self, error_groups: List[Dict[str, Any]]) -> str:
        """Format error details as HTML"""
        
        max_errors = self.config.get("max_errors_in_email", 20)
        truncate = self.config.get("truncate_long_messages", True)
        max_length = self.config.get("max_message_length", 500)
        
        html_parts = ["<table>"]
        html_parts.append(
            "<tr>"
            "<th>Service</th>"
            "<th>Error Type</th>"
            "<th>Category</th>"
            "<th>Count</th>"
            "<th>Severity</th>"
            "<th>Time Range</th>"
            "</tr>"
        )
        
        for group in error_groups[:max_errors]:
            severity_class = group.get("severity", "LOW").lower()
            
            html_parts.append(
                f"<tr>"
                f"<td>{group.get('service_name', 'Unknown')}</td>"
                f"<td>{group.get('error_type', 'Unknown')}</td>"
                f"<td>{group.get('category', 'Unknown')}</td>"
                f"<td>{group.get('count', 0)}</td>"
                f"<td class='{severity_class}'>{group.get('severity', 'LOW')}</td>"
                f"<td>{group.get('first_occurrence', 'N/A')[:19]}</td>"
                f"</tr>"
            )
        
        if len(error_groups) > max_errors:
            html_parts.append(
                f"<tr><td colspan='6'><em>... and {len(error_groups) - max_errors} more error groups</em></td></tr>"
            )
        
        html_parts.append("</table>")
        
        return "".join(html_parts)
    
    def _format_rca(self, rca_result: Dict[str, Any]) -> str:
        """Format RCA as HTML"""
        
        root_causes = rca_result.get("root_causes", [])
        
        if not root_causes:
            return "<p>No root cause identified. Manual investigation required.</p>"
        
        html_parts = []
        
        for i, rc in enumerate(root_causes[:3], 1):
            confidence = rc.get("confidence", 0)
            confidence_class = "high" if confidence >= 75 else "medium" if confidence >= 50 else "low"
            
            html_parts.append(f"<div class='error-item'>")
            html_parts.append(f"<h3>Root Cause #{i}</h3>")
            html_parts.append(f"<p><strong>Description:</strong> {rc.get('description', 'Unknown')}</p>")
            html_parts.append(f"<p><strong>Confidence:</strong> <span class='{confidence_class}'>{confidence}%</span></p>")
            
            if rc.get("affected_services"):
                html_parts.append(
                    f"<p><strong>Affected Services:</strong> {', '.join(rc['affected_services'])}</p>"
                )
            
            if rc.get("contributing_factors"):
                html_parts.append("<p><strong>Contributing Factors:</strong></p><ul>")
                for factor in rc["contributing_factors"]:
                    html_parts.append(f"<li>{factor}</li>")
                html_parts.append("</ul>")
            
            html_parts.append("</div>")
        
        return "".join(html_parts)
    
    def _format_solutions(self, solutions: Dict[str, Any]) -> str:
        """Format solutions as HTML"""
        
        solution_list = solutions.get("solutions", [])
        
        if not solution_list:
            return "<p>No automated solutions available. Manual remediation required.</p>"
        
        html_parts = []
        
        for i, solution in enumerate(solution_list[:3], 1):
            confidence = solution.get("confidence", 0)
            confidence_class = "high" if confidence >= 75 else "medium" if confidence >= 50 else "low"
            
            html_parts.append(f"<div class='solution'>")
            html_parts.append(f"<h3>Solution #{i}</h3>")
            html_parts.append(f"<p><strong>For:</strong> {solution.get('root_cause', 'Unknown')}</p>")
            html_parts.append(f"<p><strong>Confidence:</strong> <span class='{confidence_class}'>{confidence}%</span></p>")
            html_parts.append(f"<p><strong>Estimated Time:</strong> {solution.get('estimated_time', 'Unknown')}</p>")
            
            # Immediate actions
            if solution.get("immediate_actions"):
                html_parts.append("<p><strong>Immediate Actions:</strong></p><ol>")
                for action in solution["immediate_actions"]:
                    html_parts.append(f"<li>{action}</li>")
                html_parts.append("</ol>")
            
            # Preventive measures
            if solution.get("preventive_measures"):
                html_parts.append("<p><strong>Preventive Measures:</strong></p><ul>")
                for measure in solution["preventive_measures"]:
                    html_parts.append(f"<li>{measure}</li>")
                html_parts.append("</ul>")
            
            # Risks
            if solution.get("risks"):
                html_parts.append("<p><strong>Risks:</strong></p><ul>")
                for risk in solution["risks"]:
                    html_parts.append(f"<li>{risk}</li>")
                html_parts.append("</ul>")
            
            html_parts.append("</div>")
        
        # Best practices
        best_practices = solutions.get("best_practices", [])
        if best_practices:
            html_parts.append("<div class='section'>")
            html_parts.append("<h3>General Best Practices</h3>")
            html_parts.append("<ul>")
            for practice in best_practices:
                html_parts.append(f"<li>{practice}</li>")
            html_parts.append("</ul>")
            html_parts.append("</div>")
        
        return "".join(html_parts)
    
    def _parse_recipients(self) -> List[str]:
        """Parse recipient list from config"""
        
        recipients_str = self.config.get("recipients", "")
        
        if not recipients_str:
            raise EmailSenderException(
                "No email recipients configured",
                {"config_key": "recipients"}
            )
        
        # Split by comma and clean
        recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]
        
        return recipients
    
    def _send_email(self, recipients: List[str], subject: str, html_body: str):
        """Send email via SMTP"""
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.config.get('from_name', 'Log Analysis')} <{self.config['from_address']}>"
            msg["To"] = ", ".join(recipients)
            
            # Attach HTML body
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)
            
            # Connect to SMTP server
            smtp_host = self.config["host"]
            smtp_port = int(self.config["port"])
            use_tls = self.config.get("use_tls", True)
            
            if use_tls:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=self.config.get("timeout", 30))
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=self.config.get("timeout", 30))
            
            # Login
            server.login(self.config["username"], self.config["password"])
            
            # Send email
            server.sendmail(self.config["from_address"], recipients, msg.as_string())
            
            # Close connection
            server.quit()
            
            logger.info(
                "Email sent via SMTP",
                extra={
                    "recipients": recipients,
                    "subject": subject
                }
            )
        
        except smtplib.SMTPAuthenticationError as e:
            raise SMTPAuthenticationError(
                "SMTP authentication failed",
                {"host": smtp_host, "error": str(e)}
            )
        
        except smtplib.SMTPException as e:
            raise EmailSendError(
                "Failed to send email",
                {"error": str(e)}
            )
        
        except Exception as e:
            raise SMTPConnectionError(
                "SMTP connection failed",
                {"host": smtp_host, "port": smtp_port, "error": str(e)}
            )
    
    def send_test_email(self, recipient: Optional[str] = None) -> bool:
        """Send a test email"""
        
        try:
            recipients = [recipient] if recipient else self._parse_recipients()
            
            subject = "[Test] Agentic Log Analysis System - Test Email"
            html_body = """
            <html>
            <body>
                <h1>Test Email</h1>
                <p>This is a test email from the Agentic Log Analysis System.</p>
                <p>If you received this, email configuration is working correctly.</p>
                <p>Timestamp: {}</p>
            </body>
            </html>
            """.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
            
            self._send_email(recipients, subject, html_body)
            
            logger.info("Test email sent successfully")
            return True
        
        except Exception as e:
            logger.error(f"Test email failed: {e}", exc_info=True)
            return False


# CLI for testing
if __name__ == "__main__":
    import sys
    
    if "--send-test-email" in sys.argv:
        print("Sending test email...")
        agent = EmailSenderAgent()
        if agent.send_test_email():
            print("Test email sent successfully!")
        else:
            print("Test email failed!")
        sys.exit(0)
    
    if "--test" in sys.argv:
        print("Testing Email Sender Agent...")
        print("Use --send-test-email to send an actual test email")
