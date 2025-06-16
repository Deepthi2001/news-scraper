# email_sender.py

import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get email configuration from environment variables
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

def send_email(subject, body):
    if not all([SENDER_EMAIL, SENDER_PASSWORD]):
        raise ValueError("Email configuration is incomplete. Please check your .env file.")

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = os.getenv('RECIPIENT_EMAIL')  # Get recipient from environment
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, msg['To'], text)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def format_email_body():
    """Format the email body with scraped content from the JSON file."""
    try:
        with open("output.json", "r") as file:
            data = json.load(file)
    except Exception as e:
        return f"Error loading news data: {e}"
    
    body = "Today's Top News Headlines:\n\n"
    count = 0
    
    for source, source_data in data["newspapers"].items():
        for article in source_data.get("articles", []):
            if count >= 10:
                break
            title = article.get("title", "No title")
            summary = article.get("text", "").strip().replace("\n", " ")[:300]
            link = article.get("link", "")
            published = article.get("published", "")

            body += f"{count + 1}. {title}\n"
            body += f"Published: {published}\n"
            body += f"{summary}...\n"
            body += f"Read more: {link}\n\n"

            count += 1
    
    body += "\n---\n"
    body += "This is an automated news digest. To unsubscribe, please reply with 'UNSUBSCRIBE'."
    return body

def job():
    """Send the daily news report at 8 AM."""
    subject = f"Top News - {datetime.today().strftime('%Y-%m-%d')}"
    body = format_email_body()
    send_email(subject, body)

if __name__ == "__main__":
    job()
