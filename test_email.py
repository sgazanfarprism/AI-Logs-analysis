"""
Test email sending directly
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set credentials
os.environ["SMTP_HOST"] = "smtp.gmail.com"
os.environ["SMTP_PORT"] = "587"
os.environ["SMTP_USERNAME"] = "syedgazanfar.offical@gmail.com"
os.environ["SMTP_PASSWORD"] = "fwkl tqqa kmct xxmh"
os.environ["ALERT_RECIPIENTS"] = "gazanfar.syed@prismxai.com"

print("Testing email configuration...")
print(f"From: {os.environ['SMTP_USERNAME']}")
print(f"To: {os.environ['ALERT_RECIPIENTS']}")
print(f"SMTP: {os.environ['SMTP_HOST']}:{os.environ['SMTP_PORT']}")
print()

try:
    # Create message
    msg = MIMEMultipart()
    msg['Subject'] = "Test Email - AI Log Analysis System"
    msg['From'] = os.environ['SMTP_USERNAME']
    msg['To'] = os.environ['ALERT_RECIPIENTS']
    
    # Add body
    body = """
    <html>
    <body>
        <h2>Test Email</h2>
        <p>This is a test email from the AI Log Analysis System.</p>
        <p>If you receive this, email configuration is working correctly.</p>
        <p>Timestamp: """ + str(os.popen('date /t & time /t').read()) + """</p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html'))
    
    print("Connecting to SMTP server...")
    server = smtplib.SMTP(os.environ['SMTP_HOST'], int(os.environ['SMTP_PORT']), timeout=30)
    server.set_debuglevel(1)  # Show debug output
    
    print("\nStarting TLS...")
    server.starttls()
    
    print("\nLogging in...")
    server.login(os.environ['SMTP_USERNAME'], os.environ['SMTP_PASSWORD'])
    
    print("\nSending email...")
    server.sendmail(
        os.environ['SMTP_USERNAME'],
        [os.environ['ALERT_RECIPIENTS']],
        msg.as_string()
    )
    
    server.quit()
    
    print("\n✅ SUCCESS! Email sent successfully!")
    print(f"Check your inbox at: {os.environ['ALERT_RECIPIENTS']}")
    print("Also check spam/junk folder if not in inbox.")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
