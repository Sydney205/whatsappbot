# WhatsApp AI Bot with Google ADK

A FastAPI-based WhatsApp webhook server integrated with Google's AI Development Kit (ADK) and Gemini AI. The bot responds to messages containing the trigger word "bot" with intelligent, context-aware responses powered by Gemini AI with Google Search capabilities.

## Features

- **FastAPI Server**: Lightweight, fast webhook server
- **WhatsApp Cloud API Integration**: Receives and sends messages via WhatsApp
- **Google ADK Agent**: Intelligent AI agent using Gemini 2.0 with Google Search tool
- **Trigger Word Detection**: Only responds when "bot" is mentioned in the message
- **Environment-based Configuration**: Secure API key management

## Architecture

The application uses Google's ADK (AI Development Kit) with:
- **Agent**: `helpful_assistant` - A Gemini-powered agent
- **Runner**: `InMemoryRunner` - Executes agent interactions
- **Tools**: `google_search` - Enables real-time information lookup

## API Endpoints

- `GET /whatsapp` - Webhook verification endpoint for WhatsApp
- `POST /whatsapp` - Receives incoming WhatsApp messages
- `GET /` - Health check endpoint

## Environment Variables

Required environment variables:

- `GOOGLE_API_KEY` - Your Google AI API key (get from https://makersuite.google.com/app/apikey)
- `WHATSAPP_TOKEN` - WhatsApp Business API access token
- `PHONE_NUMBER_ID` - WhatsApp Business phone number ID
- `VERIFY_TOKEN` - Custom verification token for webhook setup

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (use Replit Secrets or `.env` file)

3. Run the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

## How It Works

1. WhatsApp sends incoming messages to the `POST /whatsapp` endpoint
2. The server checks if the message contains the trigger word "bot"
3. If detected, the message is passed to the `run_agent()` function
4. The Google ADK agent processes the message using Gemini AI
5. The agent can use Google Search for current information
6. The response is sent back to the user via WhatsApp Cloud API

## Example Usage

User sends: "Hey bot, what's the weather in New York today?"

The bot will:
1. Detect the trigger word "bot"
2. Use Google Search (if needed) to get current weather info
3. Generate a helpful response using Gemini AI
4. Send the response back to the user on WhatsApp
