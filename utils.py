import smtplib
import imaplib
import email
import csv
import openai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from functions import classify_response, bot_reply
import time

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
openai_client = openai.Client()

SMTP_PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

HTML_TEMPLATE = """
<html>
<body>
  <h1>Hire Faster with Us</h1>
  <p>Discover how our solution can help you streamline your hiring process. 
  Check out more details at <a href='https://example.com'>this link</a>.</p>
  <p>If you no longer wish to receive emails, <a href="https://example.com/unsubscribe">unsubscribe here</a>.</p>
</body>
</html>
"""

TEXT_TEMPLATE = """
Hire Faster with Us!

Discover how our solution can help you streamline your hiring process.
Check out more details at https://example.com.

If you no longer wish to receive emails, unsubscribe here: https://example.com/unsubscribe
"""

def get_smtp_server(email_domain):
    domain_to_smtp = {
        'gmail.com': 'smtp.gmail.com',
        'yahoo.com': 'smtp.mail.yahoo.com',
        'outlook.com': 'smtp-mail.outlook.com',
    }
    return domain_to_smtp.get(email_domain, 'smtp.example.com')

def get_imap_server(email_domain):
    domain_to_imap = {
        'gmail.com': 'imap.gmail.com',
        'yahoo.com': 'imap.mail.yahoo.com',
        'outlook.com': 'imap-mail.outlook.com',
    }
    return domain_to_imap.get(email_domain, 'imap.example.com')

def send_email_agent(recipient_email):
    email_domain = recipient_email.split('@')[1]
    smtp_server = get_smtp_server(email_domain)
    
    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_email
    msg['Subject'] = "Discover how to hire faster!"
    msg['Reply-To'] = EMAIL_USER

    msg.attach(MIMEText(TEXT_TEMPLATE, 'plain'))
    msg.attach(MIMEText(HTML_TEMPLATE, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, recipient_email, msg.as_string())
        server.quit()
        print(f"Promotional email sent to {recipient_email}")
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {str(e)}")

def reply_agent():
    email_domain = EMAIL_USER.split('@')[1]
    imap_server = get_imap_server(email_domain)
    
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select('inbox')

    _, data = mail.search(None, '(UNSEEN)')
    email_ids = data[0].split()

    for e_id in email_ids:
        _, email_data = mail.fetch(e_id, '(RFC822)')
        raw_email = email_data[0][1].decode('utf-8')
        msg = email.message_from_string(raw_email)
        sender = msg['from']
        body = get_body(msg)
        
        response_category = classify_response(body)
        print(f"Received email from {sender} classified as {response_category}")
        save_to_csv(sender, body, response_category)
        send_reply(sender, response_category)

    mail.logout()

def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                return part.get_payload(decode=True).decode('utf-8')
    else:
        return msg.get_payload(decode=True).decode('utf-8')

def save_to_csv(sender, body, category):
    file_exists = os.path.isfile('responses.csv')
    with open('responses.csv', 'a', newline='') as csvfile:
        fieldnames = ['Sender', 'Response', 'Category']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({'Sender': sender, 'Response': body, 'Category': category})
    print(f"Saved response from {sender} to CSV.")

def send_reply(recipient_email, category):
    try:
        data = bot_reply(category)
        email_domain = EMAIL_USER.split('@')[1]
        smtp_server = get_smtp_server(email_domain)
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = recipient_email
        msg['Subject'] = data['subject']
        msg.attach(MIMEText(data['body'], 'plain'))

        with smtplib.SMTP(smtp_server, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, recipient_email, msg.as_string())
        
        print(f"Reply sent to {recipient_email} for {category} response")
    except Exception as e:
        print(f"Error in send_reply: {str(e)}")

if __name__ == "__main__":
    clients = ['divyansh.academic@gmail.com']
    for client in clients:
        send_email_agent(client)
        time.sleep(10)
    # reply_agent()