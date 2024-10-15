import openai
from dotenv import load_dotenv
import os
import json

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
openai_client = openai.Client()

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
    
def bot_reply(category):
    prompt = f"Compose an email response for the category: '{category}'. Return the subject and body of the email in a json value like this: {{\"subject\": \"Subject here\", \"body\": \"Body here\"}}. ALWAYS RETURN A SINGLE LINE JSON AND NOTHING ELSE."
    
    response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Professional Email Writer, that specializes in writing email based on the user response category. You always return a single line JSON with the subject and body of the email."},
                {"role": "user", "content": prompt}
            ],
            temperature=1
        )

    content = response.choices[0].message.content.strip()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON: {content}")
        data = {
                "subject": f"Response to your {category} email",
                "body": f"Thank you for your {category} response. We have received your message and will process it accordingly."
            }

        print(f"Parsed data: {data}")
    return data