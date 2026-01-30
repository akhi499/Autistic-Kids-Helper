import os
from google import genai
from google.genai import types

# Try to load from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

# Initialize Gemini client with API key from environment variable
# Set GEMINI_API_KEY environment variable or create a .env file
api_key = os.getenv('GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY')
client = genai.Client(api_key=api_key) if api_key != 'YOUR_GEMINI_API_KEY' else None

def analyze_interaction(user_text, scenario):
    """
    Handles the 'Social Practice Gap' by checking for tone 
    before generating a response. [cite: 20, 40]
    Uses Google Gemini API.
    """
    
    # Check if API key is configured
    if client is None or api_key == 'YOUR_GEMINI_API_KEY':
        return {
            "status": "error",
            "reply": "⚠️ Gemini API key not configured. Please set the GEMINI_API_KEY environment variable.",
            "mood": "NEUTRAL"
        }
    
    try:
        # 1. PRE-SEND VIBE CHECK (Preventative) [cite: 40, 150]
        vibe_system_prompt = (
            "You are a social skills coach. Analyze if the user's message is "
            "rude, aggressive, or inappropriate for a child. "
            "Reply ONLY with 'FLAG' or 'PASS'."
        )
        
        vibe_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=vibe_system_prompt,
            ),
        )

        vibe_text = (vibe_response.text or "").strip().upper()

        if "FLAG" in vibe_text:
            return {
                "status": "flagged",
                "feedback": "That might sound a bit mean. How about we try a different way?"
            }

        # 2. ADAPTIVE ROLEPLAY (The Sandbox) [cite: 37, 43]
        # Scenarios: Grocery Store, Playground, Classroom [cite: 94]
        roleplay_prompt = (
            f"You are a friendly character in a {scenario}. "
            "Respond to the child. At the end of your message, "
            "add one of these tags based on your reaction: [HAPPY], [NEUTRAL], or [SAD]."
        )

        ai_reply = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=roleplay_prompt,
            ),
        )

        content = (ai_reply.text or "").strip()
        
        # Extract Mood for the Visual-First interface [cite: 148]
        mood = "NEUTRAL"
        if "[HAPPY]" in content:
            mood = "HAPPY"
        elif "[SAD]" in content:
            mood = "SAD"
        
        clean_text = content.replace("[HAPPY]", "").replace("[SAD]", "").replace("[NEUTRAL]", "").strip()

        return {
            "status": "success",
            "reply": clean_text,
            "mood": mood
        }
    
    except Exception as e:
        # Return error message instead of crashing
        return {
            "status": "error",
            "reply": f"⚠️ Error: {str(e)}",
            "mood": "NEUTRAL"
        }
