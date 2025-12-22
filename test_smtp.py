"""
Simple SMTP test for Gmail configuration
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail SMTP settings
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "syedgazanfar.offical@gmail.com"
SMTP_PASSWORD = "fwkl tqqa kmct xxmh"
RECIPIENT = "syedgazanfar.offical@gmail.com"

print("=" * 60)
print("GMAIL SMTP CONNECTION TEST")
print("=" * 60)

try:
    print("\n1. Creating email message...")
    msg = MIMEMultipart()
    msg["Subject"] = "[Test] Agentic Log Analysis - SMTP Test"
    msg["From"] = f"Agentic Log Analysis <{SMTP_USERNAME}>"
    msg["To"] = RECIPIENT
    
    html_body = """
    <html>
    <body>
        <h2>SMTP Configuration Test</h2>
        <p>This is a test email from the Agentic AI Log Analysis System.</p>
        <p><strong>Status:</strong> Email configuration is working correctly!</p>
        <p><strong>SMTP Server:</strong> smtp.gmail.com:587</p>
        <p><strong>Timestamp:</strong> 2025-12-20 22:18:35 UTC</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            This is an automated test email. If you received this, your SMTP configuration is correct.
        </p>
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
    
    print("\n5. Sending test email...")
    server.sendmail(SMTP_USERNAME, [RECIPIENT], msg.as_string())
    print("   ✓ Email sent successfully")
    
    print("\n6. Closing connection...")
    server.quit()
    print("   ✓ Connection closed")
    
    print("\n" + "=" * 60)
    print("✅ SMTP TEST PASSED")
    print("=" * 60)
    print(f"\nTest email sent to: {RECIPIENT}")
    print("Check your inbox to confirm receipt.")
    print("\nYour SMTP configuration is working correctly!")
    print("The Agentic Log Analysis System is ready to send email alerts.")
    
except smtplib.SMTPAuthenticationError as e:
    print("\n" + "=" * 60)
    print("❌ AUTHENTICATION FAILED")
    print("=" * 60)
    print(f"\nError: {e}")
    print("\nTroubleshooting:")
    print("1. Verify your Gmail app password is correct")
    print("2. Ensure 2-Factor Authentication is enabled on your Google account")
    print("3. Generate a new app password at: https://myaccount.google.com/apppasswords")
    print("4. Make sure you're using the app password, not your regular Gmail password")
    
except smtplib.SMTPException as e:
    print("\n" + "=" * 60)
    print("❌ SMTP ERROR")
    print("=" * 60)
    print(f"\nError: {e}")
    print("\nCheck your SMTP settings and try again.")
    
except Exception as e:
    print("\n" + "=" * 60)
    print("❌ TEST FAILED")
    print("=" * 60)
    print(f"\nError: {e}")
    print("\nPlease check your configuration and try again.")
