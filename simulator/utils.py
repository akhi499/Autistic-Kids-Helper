import os
from mistralai import Mistral

# Try to load from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

# Initialize Mistral client with API key from environment variable
# Set MISTRAL_API_KEY environment variable or create a .env file
api_key = os.getenv('MISTRAL_API_KEY', 'YOUR_MISTRAL_API_KEY')
client = Mistral(api_key=api_key) if api_key != 'YOUR_MISTRAL_API_KEY' else None

def analyze_interaction(user_text, scenario):
    """
    Handles the 'Social Practice Gap' by checking for tone 
    before generating a response. [cite: 20, 40]
    Uses Mistral AI API.
    """
    
    # Check if API key is configured
    if client is None or api_key == 'YOUR_MISTRAL_API_KEY':
        return {
            "status": "error",
            "reply": "⚠️ Mistral API key not configured. Please set the MISTRAL_API_KEY environment variable.",
            "mood": "NEUTRAL"
        }
    
    try:
        # 1. PRE-SEND VIBE CHECK (Preventative) [cite: 40, 150]
        # Only flag clearly harmful content; allow mild negativity and normal emotions
        vibe_system_prompt = (
            "You are a filter for a child's social practice app. Reply ONLY with 'FLAG' or 'PASS'.\n\n"
            "FLAG only if the message is: insults or name-calling, threats, swear words, "
            "deliberately mean or cruel, or clearly inappropriate for a child (e.g. adult topics).\n\n"
            "PASS for: mild frustration, annoyance, or disappointment; saying 'no' or 'I don't want to'; "
            "complaining ('this is boring', 'I'm tired'); being shy or quiet; disagreement; "
            "sadness or grumpiness; any normal negative emotion a child might express. "
            "When in doubt, choose PASS."
        )
        
        vibe_response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": vibe_system_prompt},
                {"role": "user", "content": user_text}
            ]
        )

        vibe_text = (vibe_response.choices[0].message.content or "").strip().upper()

        if "FLAG" in vibe_text:
            return {
                "status": "flagged",
                "feedback": "That might sound a bit mean. How about we try a different way?",
                "suggestions": []
            }

        # 2. ADAPTIVE ROLEPLAY (The Sandbox) [cite: 37, 43]
        # Character should react honestly: get sad/upset when the child is rude or dismissive
        roleplay_prompt = (
            f"You are a friendly character in a {scenario}. Respond to the child as a real person would.\n\n"
            "Your reaction must match what they said. Use exactly one tag at the end of your message:\n"
            "- [HAPPY] if they are kind, polite, or friendly.\n"
            "- [SAD] if they are rude, dismissive, or say something that hurts your feelings—show that you're hurt.\n"
            "- [ANGRY] if they are mean, insulting, or deliberately unkind—show that you're upset.\n"
            "- [NEUTRAL] only for bland small talk or when you're not sure.\n\n"
            "If the child is rude or mean, do NOT stay neutral. React with [SAD] or [ANGRY] so they see the effect of their words."
        )

        ai_reply = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": roleplay_prompt},
                {"role": "user", "content": user_text}
            ]
        )

        content = (ai_reply.choices[0].message.content or "").strip()
        
        # Extract Mood for the Visual-First interface [cite: 148]
        mood = "NEUTRAL"
        if "[HAPPY]" in content:
            mood = "HAPPY"
        elif "[ANGRY]" in content:
            mood = "ANGRY"
        elif "[SAD]" in content:
            mood = "SAD"
        
        clean_text = content.replace("[HAPPY]", "").replace("[SAD]", "").replace("[ANGRY]", "").replace("[NEUTRAL]", "").strip()

        # 3. SUGGESTED RESPONSES (dialogue-based: what the child could say next)
        suggestions_prompt = (
            f"Scenario: {scenario}. The character just said: \"{clean_text[:200]}\"\n\n"
            "Suggest exactly 4 short phrases a child might say next in this conversation (friendly, polite, or asking for help). "
            "One phrase per line, no numbers or bullets. Keep each under 10 words."
        )
        try:
            sugg_response = client.chat.complete(
                model="mistral-small-latest",
                messages=[
                    {"role": "system", "content": "Reply with only 4 short phrases, one per line. No numbering."},
                    {"role": "user", "content": suggestions_prompt}
                ]
            )
            raw = (sugg_response.choices[0].message.content or "").strip()
            suggestions = [line.strip() for line in raw.split("\n") if line.strip()][:5]
            suggestions = [s.lstrip(".-)0123456789 ") for s in suggestions]  # drop leading numbers/bullets
        except Exception:
            suggestions = []

        return {
            "status": "success",
            "reply": clean_text,
            "mood": mood,
            "suggestions": suggestions if suggestions else ["Hi!", "Thank you", "Can you help me?", "Sorry"]
        }
    
    except Exception as e:
        # Return error message instead of crashing
        return {
            "status": "error",
            "reply": f"⚠️ Error: {str(e)}",
            "mood": "NEUTRAL",
            "suggestions": []
        }
