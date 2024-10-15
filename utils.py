import smtplib
import imaplib
import email
import csv
import openai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
openai_client = openai.Client()

SMTP_PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

HTML_TEMPLATE = """
<html>
<body>
  <h1>Hire Faster with us</h1>
  <p>Check out our amazing product at <a href='https://example.com'>this link</a>!</p>
</body>
</html>
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

def send_email(recipient_email):
    email_domain = recipient_email.split('@')[1]
    smtp_server = get_smtp_server(email_domain)
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_email
    msg['Subject'] = "Test Email"

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

def check_inbox():
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

def classify_response(text):
    prompt = f"Classify the following email response into one of the following categories: positive, unsubscribe, inquiry, other. '{text}'"
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Professional Email Categoriser, that specializes in categorizing email responses into positive, unsubscribe, inquiry, other."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        category = response.choices[0].message.content.strip().lower()
        return category
    except Exception as e:
        print(f"Error classifying response: {str(e)}")
        return "other"

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
    if category == "positive":
        subject = "Thank you for your interest!"
        body = "We are glad you are interested in our product. Feel free to reach out for more details."
    elif category == "unsubscribe":
        subject = "Unsubscribed from our mailing list"
        body = "We have removed you from our mailing list. Thank you!"
    elif category == "inquiry":
        subject = "More Information About Our Product"
        body = "We appreciate your interest. Here's more information on the product you asked about."
    else:
        subject = "Thank you for your feedback"
        body = "We have received your message. Thank you for your feedback."

    email_domain = EMAIL_USER.split('@')[1]  # Use sender's email domain
    smtp_server = get_smtp_server(email_domain)
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, recipient_email, msg.as_string())
        server.quit()
        print(f"Reply sent to {recipient_email} for {category} response")
    except Exception as e:
        print(f"Error sending reply: {str(e)}")

if __name__ == "__main__":
    # clients = ['ishkirat04@gmail.com']
    # for client in clients:
    #     send_email(client)
    check_inbox()
