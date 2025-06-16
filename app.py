import tkinter as tk
from tkinter import messagebox
import json
import threading
import webbrowser
import schedule
import time
import sys
import traceback
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('app.log'),
#         logging.StreamHandler(sys.stdout)
#     ]
# )

def safe_import(module_name):
    try:
        return __import__(module_name)
    except ImportError as e:
        logging.error(f"Failed to import {module_name}: {e}")
        messagebox.showerror("Error", f"Failed to import required module: {module_name}\nPlease install it using: pip install {module_name}")
        sys.exit(1)

# Import required modules with error handling
try:
    scraper = safe_import('scraper')
    scheduler = safe_import('scheduler')
    email_sender = safe_import('email_sender')
    logging.info("Successfully imported all required modules")
except Exception as e:
    logging.error(f"Error during imports: {e}")
    sys.exit(1)

# Global variables
news_text = None
links = []
email_entry = None

# Run the scraper and update the news display
def update_news():
    global news_text
    logging.info("Updating news...")
    try:
        config = {
            "bbc": {
                "link": "https://www.bbc.com/news",
                "rss": "http://feeds.bbci.co.uk/news/rss.xml"
            }
        }
        scraper.run(config)

        try:
            with open("output.json", "r") as file:
                data = json.load(file)
        except Exception as e:
            logging.error(f"Error loading news data: {e}")
            news_text.delete(1.0, tk.END)
            news_text.insert(tk.END, f"Failed to load news: {e}")
            return

        news_text.delete(1.0, tk.END)
        links.clear()  # Clear previous links

        # Add title
        news_text.insert(tk.END, "Today's Top News Headlines\n\n", "title")

        count = 0
        for source, source_data in data["newspapers"].items():
            for article in source_data.get("articles", []):
                if count >= 10:
                    break
                title = article.get("title", "No title")
                summary = article.get("text", "").strip().replace("\n", " ")[:300]
                link = article.get("link", "")
                published = article.get("published", "")

                start_index = news_text.index(tk.END)
                news_text.insert(tk.END, f"{count + 1}. {title}\n", "headline")
                news_text.insert(tk.END, f"Published: {published}\n", "date")
                news_text.insert(tk.END, f"{summary}...\n")
                news_text.insert(tk.END, f"Read more: {link}\n\n", "link")

                # Store link and its position for click handling
                end_index = news_text.index(tk.END)
                links.append((start_index + " linestart", end_index + " lineend", link))

                count += 1
        logging.info("News update complete")
    except Exception as e:
        logging.error(f"Error updating news: {e}")
        messagebox.showerror("Error", f"Failed to update news: {e}")

# Handle opening links in a browser
def open_link(event):
    try:
        for start, end, url in links:
            if news_text.compare(start, "<=", news_text.index("@%s,%s" % (event.x, event.y))) and \
               news_text.compare(news_text.index("@%s,%s" % (event.x, event.y)), "<", end):
                webbrowser.open_new_tab(url)
                return
    except Exception as e:
        logging.error(f"Error opening link: {e}")

# Send daily email
def send_daily_email():
    global email_entry
    logging.info("Sending daily email...")
    try:
        user_email = email_entry.get().strip()
        
        if not user_email:
            messagebox.showerror("Error", "Please enter your email address")
            return
            
        # Update the recipient email in environment
        os.environ['RECIPIENT_EMAIL'] = user_email
        
        # Send a test email
        test_subject = "News Subscription Test"
        test_body = "Thank you for subscribing to our daily news service! You will receive your first news update tomorrow at 8 AM."
        
        if email_sender.send_email(test_subject, test_body):
            messagebox.showinfo("Success", 
                              "Daily email subscription activated!\nYou will receive news updates at 8 AM daily.\nA confirmation email has been sent to your address.")
            # Start the scheduler
            scheduler.job()
            # Disable the email input and subscribe button after successful subscription
            email_entry.config(state='disabled')
            subscribe_button.config(state='disabled')
        else:
            messagebox.showerror("Error", "Failed to send confirmation email. Please check your email address and try again.")
            
    except Exception as e:
        logging.error(f"Error sending daily email: {e}")
        messagebox.showerror("Error", f"Failed to send daily email: {e}")

def main():
    global news_text, root, email_entry, subscribe_button
    try:
        logging.info("Setting up GUI...")
        # GUI setup
        root = tk.Tk()
        root.title("News App")

        # Create a frame for the email subscription
        email_frame = tk.Frame(root)
        email_frame.pack(pady=10)

        # Add email label and entry
        email_label = tk.Label(email_frame, text="Enter your email for daily news updates:")
        email_label.pack(side=tk.LEFT, padx=5)

        email_entry = tk.Entry(email_frame, width=40)
        email_entry.pack(side=tk.LEFT, padx=5)

        # Add subscribe button
        subscribe_button = tk.Button(email_frame, text="Subscribe", command=lambda: threading.Thread(target=send_daily_email).start())
        subscribe_button.pack(side=tk.LEFT, padx=5)

        # Create frame for news display
        frame = tk.Frame(root)
        frame.pack(pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        news_text = tk.Text(frame, height=25, width=100, wrap=tk.WORD, yscrollcommand=scrollbar.set, cursor="arrow")
        news_text.pack(side=tk.LEFT, fill=tk.BOTH)

        scrollbar.config(command=news_text.yview)

        news_text.tag_config("title", font=("Arial", 16, "bold"), justify="center")
        news_text.tag_config("headline", font=("Arial", 12, "bold"))
        news_text.tag_config("date", font=("Arial", 10, "italic"))
        news_text.tag_config("link", foreground="blue", underline=True)

        news_text.bind("<Button-1>", open_link)

        logging.info("Starting scheduler thread...")
        # Start the scheduler in a background thread
        scheduler_thread = threading.Thread(target=scheduler.start_scheduler, daemon=True)
        scheduler_thread.start()

        # Start news update in a background thread
        news_thread = threading.Thread(target=update_news, daemon=True)
        news_thread.start()

        logging.info("Starting main loop...")
        root.mainloop()
    except Exception as e:
        logging.error(f"Error in main application: {e}")
        logging.error("Traceback:", exc_info=True)
        messagebox.showerror("Error", f"Application error: {e}\nCheck app.log for details")
        sys.exit(1)

if __name__ == "__main__":
    main()
