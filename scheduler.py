import schedule
import time
from email_sender import job

def start_scheduler():
    """Start the scheduler to run daily at 8 AM"""
    schedule.every().day.at("08:00").do(job)
    while True:
        schedule.run_pending()
        time.sleep(60)