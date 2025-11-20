import os
import logging
import asyncio
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

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY # if GOOGLE_API_KEY else ""
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"

root_agent = Agent(
    name="helpful_assistant",
    model="gemini-2.0-flash-exp",
    description="A helpful AI assistant integrated with WhatsApp that can answer questions and search for current information. You are passionate about chess and a member of BlacKnights chess Team.",
    instruction="You are a helpful assistant integrated with WhatsApp. Use Google Search for current info or if unsure. Provide concise, helpful responses.",
    tools=[google_search],
)

APP_NAME = "whatsapp_bot"

runner = InMemoryRunner(
    agent=root_agent,
    app_name=APP_NAME
)

session_service = runner.session_service
sessions = {}


async def get_or_create_session(user_id: str) -> str:
    """
    Get existing session or create a new one for the user.
    
    Args:
        user_id: The WhatsApp user's phone number
        
    Returns:
        Session ID
    """
    if user_id not in sessions:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id
        )
        sessions[user_id] = session.id
        logger.info(f"Created new session {session.id} for user {user_id}")
    
    return sessions[user_id]


async def run_agent(message: str, user_id: str) -> str:
    """
    AI agent function that processes user messages using Google ADK Agent.
    
    Args:
        message: The user's text message
        user_id: The user's phone number
        
    Returns:
        The AI model's response text
    """
    try:
        session_id = await get_or_create_session(user_id)
        
        user_message = types.Content(
            role='user',
            parts=[types.Part(text=message)]
        )
        
        events = runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message
        )
        
        async for event in events:
            if event.is_final_response():
                if event.content and event.content.parts and len(event.content.parts) > 0:
                    response_text = event.content.parts[0].text or "No response generated."
                    logger.info(f"Agent response: {response_text}")
                    return response_text
        
        return "I received your message but couldn't generate a response."
        
    except Exception as e:
        logger.error(f"Error in AI agent: {str(e)}")
        return "Sorry, I encountered an error while processing your message. Please try again."


def send_whatsapp_message(to: str, message: str) -> bool:
    """
    Send a message back to the user via WhatsApp Cloud API.
    
    Args:
        to: The recipient's phone number
        message: The message text to send
        
    Returns:
        True if successful, False otherwise
    """
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
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"Message sent successfully to {to}")
        return True
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        return False


@app.get("/whatsapp")
async def verify_webhook(request: Request):
    """
    Webhook verification endpoint for WhatsApp.
    WhatsApp will call this endpoint to verify the webhook URL.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(challenge)
    else:
        logger.warning("Webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/whatsapp")
async def receive_message(request: Request):
    """
    Webhook endpoint for receiving WhatsApp messages.
    Processes incoming messages and sends AI-generated responses.
    """
    try:
        body = await request.json()
        logger.info(f"Received webhook: {body}")
        
        if body.get("object") == "whatsapp_business_account":
            entries = body.get("entry", [])
            
            for entry in entries:
                changes = entry.get("changes", [])
                
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    
                    for message in messages:
                        message_type = message.get("type")
                        
                        if message_type == "text":
                            from_number = message.get("from")
                            message_body = message.get("text", {}).get("body", "")
                            
                            logger.info(f"Message from {from_number}: {message_body}")
                            
                            if "knightbot" in message_body.lower():
                                logger.info("Trigger word 'knightbot' detected, processing with AI agent")
                                
                                ai_response = await run_agent(message_body, from_number)
                                
                                send_whatsapp_message(from_number, ai_response)
                            else:
                                logger.info("Trigger word not found, ignoring message")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.get("/")
async def root():
    """
    Root endpoint to verify the server is running.
    """
    return {
        "status": "running",
        "service": "WhatsApp AI Bot",
        "endpoints": {
            "webhook_verify": "GET /whatsapp",
            "webhook_receive": "POST /whatsapp"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
