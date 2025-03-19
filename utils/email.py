from flask_mail import Message
from extensions import mail

def send_email(to, subject, body):
    """Sends an email using Flask-Mail."""
    msg = Message(subject=subject, recipients=[to], body=body)
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
