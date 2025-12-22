"""
Send test email to specific recipient
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail SMTP settings
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "syedgazanfar.offical@gmail.com"
SMTP_PASSWORD = "fwkl tqqa kmct xxmh"
RECIPIENT = "gazanfar.syed@prismxai.com"

print("=" * 60)
print("SENDING TEST EMAIL")
print("=" * 60)
print(f"\nRecipient: {RECIPIENT}")

try:
    print("\n1. Creating email message...")
    msg = MIMEMultipart()
    msg["Subject"] = "[Test] Agentic AI Log Analysis System - Email Test"
    msg["From"] = f"Agentic Log Analysis <{SMTP_USERNAME}>"
    msg["To"] = RECIPIENT
    
    html_body = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; }
            .info-box { background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-left: 4px solid #4CAF50; }
            .footer { color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }
            .success { color: #4CAF50; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Agentic AI Log Analysis System</h1>
            <p>Email Configuration Test</p>
        </div>
        
        <div class="content">
            <h2>✅ Email System Test Successful</h2>
            
            <p>This is a test email from the <strong>Agentic AI Log Analysis System</strong>.</p>
            
            <div class="info-box">
                <h3>System Information</h3>
                <p><strong>Status:</strong> <span class="success">Email configuration is working correctly!</span></p>
                <p><strong>SMTP Server:</strong> smtp.gmail.com:587</p>
                <p><strong>Sender:</strong> syedgazanfar.offical@gmail.com</p>
                <p><strong>Timestamp:</strong> 2025-12-20 22:21:14 UTC</p>
            </div>
            
            <h3>What This Means</h3>
            <p>The Agentic AI Log Analysis System is now configured to send automated email alerts when errors are detected in your logs.</p>
            
            <h3>Email Alerts Will Include:</h3>
            <ul>
                <li>Error summary and statistics</li>
                <li>Affected services and severity levels</li>
                <li>AI-powered Root Cause Analysis (RCA)</li>
                <li>Recommended remediation solutions</li>
                <li>Preventive measures</li>
            </ul>
            
            <h3>Next Steps</h3>
            <ol>
                <li>Configure Elasticsearch credentials</li>
                <li>Test Gemini AI integration</li>
                <li>Run first log analysis</li>
            </ol>
        </div>
        
        <div class="footer">
            <p>This is an automated test email from the Agentic AI Log Analysis System.</p>
            <p>If you received this email, the SMTP configuration is working correctly.</p>
            <hr>
            <p>Regards,</p>
            <p><strong>Syed Gazanfar</strong></p>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_body, "html"))
    print("   ✓ Email message created")
    
    print("\n2. Connecting to Gmail SMTP server...")
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
    print("   ✓ Connected to smtp.gmail.com:587")
    
    print("\n3. Starting TLS encryption...")
    server.starttls()
    print("   ✓ TLS encryption enabled")
    
    print("\n4. Authenticating with Gmail...")
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    print("   ✓ Authentication successful")
    
    print("\n5. Sending email...")
    server.sendmail(SMTP_USERNAME, [RECIPIENT], msg.as_string())
    print("   ✓ Email sent successfully")
    
    print("\n6. Closing connection...")
    server.quit()
    print("   ✓ Connection closed")
    
    print("\n" + "=" * 60)
    print("✅ EMAIL SENT SUCCESSFULLY")
    print("=" * 60)
    print(f"\nTest email sent to: {RECIPIENT}")
    print("\nPlease check the inbox at gazanfar.syed@prismxai.com")
    print("The email should arrive within a few seconds.")
    
except Exception as e:
    print("\n" + "=" * 60)
    print("❌ FAILED TO SEND EMAIL")
    print("=" * 60)
    print(f"\nError: {e}")
