import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

MAILTRAP_HOST = "live.smtp.mailtrap.io"
MAILTRAP_PORT = 587
MAILTRAP_USERNAME =  os.getenv("MAILTRAP_USERNAME")
MAILTRAP_PASSWORD = os.getenv("MAILTRAP_PASSWORD")

sender_email = "hello@demomailtrap.com"
recipient_email = "leontescuadrian8@gmail.com"
subject = "You are awesome!"
body = "Congrats for sending a test email with Mailtrap!"

message = MIMEMultipart()
message["From"] = sender_email
message["To"] = recipient_email
message["Subject"] = subject
message.attach(MIMEText(body, "plain"))

# Send the email via Mailtrap's SMTP
try:
    with smtplib.SMTP(MAILTRAP_HOST, MAILTRAP_PORT) as server:
        server.starttls()
        server.login(MAILTRAP_USERNAME, MAILTRAP_PASSWORD)
        server.sendmail(sender_email, recipient_email, message.as_string())
        print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
