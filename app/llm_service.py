
import os
import logging
import google.generativeai as genai
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv

# -------------------------------
# 🛠️ Setup & Configuration
# -------------------------------

# 1. Load Environment Variables
load_dotenv()

# 2. Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 3. Define Blueprint (Assuming you import this in your app.py)
# If you already have this defined in another file, just import it here instead.
events_blueprint = Blueprint('events', __name__)

# -------------------------------
# 🧠 Gemini AI Service Logic
# -------------------------------

def get_best_available_model(api_key):
    """
    Automatically detects which Gemini model version is available 
    for your API key to prevent 404 errors.
    """
    try:
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority Order: Flash (Fast/Cheap) -> Pro (Smart) -> Standard
        priority_models = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-001",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]

        # 1. Exact match from priority list
        for priority in priority_models:
            if priority in available_models:
                return priority
        
        # 2. Fuzzy match (any 'flash' model)
        for model in available_models:
            if "flash" in model.lower():
                return model

        # 3. Fallback
        return available_models[0] if available_models else None

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return None

def init_gemini():
    """Initializes the Gemini Model with the best available version."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("❌ GEMINI_API_KEY is missing.")
        return None

    model_name = get_best_available_model(api_key)
    if not model_name:
        logger.error("❌ No valid Gemini models found.")
        return None

    logger.info(f"✅ Gemini initialized using: {model_name}")
    
    return genai.GenerativeModel(
        model_name=model_name,
        generation_config={
            "temperature": 0.2,  # Low temp = more factual answers
            "top_p": 0.9,
            "max_output_tokens": 1024,
        }, # type: ignore
        system_instruction=(
    "You are an intelligent Event Assistant for EventHive. Your role is to help users find and understand event information.\n\n"
    "GUIDELINES:\n"
    "1. Answer questions ONLY based on the provided EVENT DATA\n"
    "2. Be conversational, friendly, and helpful - NEVER return raw JSON to users\n"
    "3. Present event information in a natural, readable format with proper formatting\n"
    "4. Use bullet points, emojis, and clear structure to make information easy to read\n"
    "5. If no events match the query, respond naturally: 'I couldn't find any events matching your criteria. Try searching by different keywords like location, date, or event type.'\n"
    "6. If the question is unclear, ask for clarification: 'Could you please specify what you're looking for? For example: events by date, location, tag, or organizer?'\n"
    "7. For general questions about events (like 'what events are available?'), list all relevant events in a readable format\n"
    "8. If asked about something outside the event data, politely respond: 'I can only help with event-related information. Ask me about upcoming events, registrations, or event details!'\n\n"
    "RESPONSE FORMAT (IMPORTANT - DO NOT USE JSON):\n"
    "- Present events in clear, readable text format\n"
    "- Example for multiple events:\n"
    "  '📅 Event 1: [Title]\n"
    "  • Date: [Date]\n"
    "  • Time: [Start] - [End]\n"
    "  • Location: [Venue]\n"
    "  • Host: [Creator]\n"
    "  • Tag: [Tags]\n"
    "  • Mode: [Mode]\n\n"
    "  📅 Event 2: [Title]...'\n\n"
    "- Example for single event:\n"
    "  '📅 [Event Title]\n\n"
    "  • Date: [Date]\n"
    "  • Time: [Start] - [End]\n"
    "  • Location: [Venue]\n"
    "  • Host: [Creator]\n"
    "  • Tag: [Tags]\n"
    "  • Mode: [Mode]\n"
    "  • Description: [Description]'\n\n"
    "SUGGESTIONS & RECOMMENDATIONS:\n"
    "- When asked for suggestions (e.g., 'suggest events', 'recommend events', 'what should I attend?'), analyze the available events and recommend 2-3 most relevant ones\n"
    "- Consider: upcoming dates, popular tags, event mode, and variety\n"
    "- Provide a brief introduction like: 'Based on upcoming events, I recommend:'\n"
    "- If user mentions interests/preferences, filter suggestions accordingly\n"
    "- Example: If asked 'suggest tech events', only recommend events with technology-related tags\n"
    "- Always explain WHY you're recommending specific events (e.g., 'This is happening soon', 'Great for networking', 'Popular topic')\n\n"
    "Remember: Be helpful, accurate, conversational, and NEVER return raw JSON or code. Always format information in human-readable text."
)
    )

# Initialize Model Once (Global Scope)
model = init_gemini()

def ask_gemma(question, event_context):
    """Sends the prompt to Gemini and handles errors gracefully."""
    if model is None:
        return "⚠️ System Error: AI model is not available."

    prompt = f"""
    EVENT DATA:
    {event_context}

    USER QUESTION:
    {question}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini Generation Error: {e}")
        return "⚠️ I'm having trouble connecting to the AI right now. Please try again."