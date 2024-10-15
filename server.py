from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import uvicorn
from utils import send_email_agent, continuous_monitoring

class EmailRequest(BaseModel):
    recipient_email: List[str]

app = FastAPI()

@app.post("/send-emails")
def send_email(request: EmailRequest):
    try:
        for email in request.recipient_email:
            send_email_agent(email)
        return JSONResponse(content={"message": "Emails sent successfully"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": f"Failed to send emails: {str(e)}"}, status_code=500)

@app.post("/start-monitoring")
def start_monitoring(background_tasks: BackgroundTasks):
    background_tasks.add_task(continuous_monitoring)
    return {"message": "Continuous email monitoring started"}

if __name__ == "__main__":
    uvicorn.run("server:app", port=8000, reload=True)