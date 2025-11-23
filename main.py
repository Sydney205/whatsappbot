import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import requests
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"

APP_NAME = "whatsapp_bot"

root_agent = Agent(
    name="whatsapp_bot",
    model="gemini-2.0-flash-exp",
    description="WhatsApp AI Assistant",
    instruction="Respond concisely and helpfully.",
    tools=[google_search],
)

runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
session_service = runner.session_service
sessions = {}


async def get_or_create_session(user_id: str) -> str:
    if user_id not in sessions:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id
        )
        sessions[user_id] = session.id
    return sessions[user_id]


async def run_agent(message: str, user_id: str) -> str:
    try:
        session_id = await get_or_create_session(user_id)
        user_message = types.Content(role="user", parts=[types.Part(text=message)])
        
        # Important fix: use await instead of async streaming
        result = await runner.run_message(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message
        )

        if result and result.parts:
            return result.parts[0].text or "I could not generate a response."

        return "I received your message but couldn't generate a response."

    except Exception as e:
        logger.error(f"AI error: {str(e)}")
        return "Sorry, I encountered an error."


def send_whatsapp_message(to: str, message: str):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    try:
        r = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        logger.info(f"WhatsApp send response: {r.text}")
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")


@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)

    raise HTTPException(status_code=403)


@app.post("/webhook")
async def receive_message(request: Request):
    try:
        data = await request.json()
        logger.info(f"Webhook received: {data}")

        if data.get("object") != "whatsapp_business_account":
            return {"status": "ignored"}

        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for msg in messages:
                    from_number = msg.get("from")
                    text = msg.get("text", {}).get("body")

                    if from_number and text:
                        ai_reply = await run_agent(text, from_number)
                        send_whatsapp_message(from_number, ai_reply)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}