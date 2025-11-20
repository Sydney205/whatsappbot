# WhatsApp AI Bot Project

## Overview
A FastAPI-based WhatsApp webhook server integrated with Google's AI Development Kit (ADK) and Gemini AI. The bot intelligently responds to WhatsApp messages containing the trigger word "bot" using Gemini 2.0 with Google Search capabilities.

## Recent Changes
- **2024-11-17**: Initial project setup with Google ADK integration
  - Implemented FastAPI webhook server for WhatsApp Cloud API
  - Integrated Google ADK Agent with InMemoryRunner
  - Added session management for conversation context
  - Configured google_search tool for real-time information lookup

## Project Architecture

### Core Components
1. **FastAPI Server**: Handles WhatsApp webhook requests
2. **Google ADK Agent**: Processes messages using Gemini AI
3. **InMemoryRunner**: Manages agent execution and sessions
4. **Session Management**: Maintains conversation context per user

### Key Files
- `main.py`: Main application with FastAPI server and AI agent logic
- `requirements.txt`: Python dependencies
- `README.md`: User-facing documentation
- `.env.example`: Environment variable template

## Environment Variables
Required for operation:
- `GOOGLE_API_KEY`: Google AI API key for Gemini
- `WHATSAPP_TOKEN`: WhatsApp Business API access token
- `PHONE_NUMBER_ID`: WhatsApp Business phone number ID
- `VERIFY_TOKEN`: Custom webhook verification token

## Features
- Webhook verification for WhatsApp integration
- Message filtering based on trigger word "bot"
- AI-powered responses using Gemini 2.0 Flash
- Google Search integration for current information
- Session-based conversation management
- Comprehensive error handling and logging

## User Preferences
No specific user preferences recorded yet.

## Technical Decisions
- **Framework**: FastAPI chosen for async support and performance
- **AI Model**: Gemini 2.0 Flash Experimental for fast responses
- **Session Storage**: In-memory session service (suitable for development/small scale)
- **Port**: 8080 (as configured in workflow)
