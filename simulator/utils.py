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

def analyze_interaction(user_text, scenario, history=None):
    """
    Handles the 'Social Practice Gap' by checking for tone
    before generating a response. Uses conversation history so the agent
    remembers context (e.g. helping find mom, last seen near produce).
    Uses Mistral AI API.
    """
    history = history or []

    # Check if API key is configured
    if client is None or api_key == 'YOUR_MISTRAL_API_KEY':
        return {
            "status": "error",
            "reply": "⚠️ Mistral API key not configured. Please set the MISTRAL_API_KEY environment variable.",
            "mood": "NEUTRAL"
        }
    
    try:
        # 1. PRE-SEND VIBE CHECK (Preventative) [cite: 40, 150]
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

        # 2. ADAPTIVE ROLEPLAY with conversation history so the agent remembers context
        roleplay_prompt = (
            f"You are a friendly character in a {scenario}. Respond to the child as a real person would.\n\n"
            "CRITICAL - CONTINUITY: You MUST continue the same conversation. Never reset or start over.\n"
            "- If you offered to help (e.g. find their mom) and asked a question (e.g. 'Where did you last see her?'), "
            "and the child answers (e.g. 'We were in the cereal aisle'), you MUST respond to that answer—e.g. "
            "'Let's go check the cereal aisle together' or 'I'll help you look there.'\n"
            "- NEVER reply with a new generic greeting like 'Oh, hey there! What can I help you with?' when you are "
            "already in the middle of helping them. That would ignore what they just said.\n"
            "- If the child gives you information you asked for (a place, a description, etc.), use it and continue "
            "helping. Do not change the subject.\n\n"
            "Your reaction must match what they said. Use exactly one tag at the end of your message:\n"
            "- [HAPPY] ONLY when they do something clearly kind or thoughtful: saying please, thank you, "
            "sorry, giving a compliment, offering to help, including others, or showing real appreciation. "
            "Do NOT use [HAPPY] for a simple greeting like 'Hi', 'Hello', or 'Hey' by itself—use [NEUTRAL] for those.\n"
            "- [SAD] if they are rude, dismissive, or say something that hurts your feelings—show that you're hurt.\n"
            "- [ANGRY] if they are mean, insulting, or deliberately unkind—show that you're upset.\n"
            "- [NEUTRAL] for bland small talk, simple greetings, or when you're not sure.\n\n"
            "If the child is rude or mean, do NOT stay neutral. React with [SAD] or [ANGRY]. "
            "Reserve [HAPPY] for genuine kindness—polite words, appreciation, or caring—not just saying hi."
        )

        # Build messages with full conversation history so the model remembers context
        roleplay_messages = [{"role": "system", "content": roleplay_prompt}]
        for h in history:
            role = "user" if h.get("sender") == "user" else "assistant"
            text = (h.get("text") or "").strip()
            if text:
                roleplay_messages.append({"role": role, "content": text})
        # When there is history, prepend a short reminder so the model treats the next line as the child's direct reply
        if history:
            context_nudge = (
                "[The child is replying to what you last said. Respond by continuing that conversation—do not start a new one.]\n\n"
                "Child says: "
            )
            roleplay_messages.append({"role": "user", "content": context_nudge + user_text})
        else:
            roleplay_messages.append({"role": "user", "content": user_text})

        ai_reply = client.chat.complete(
            model="mistral-small-latest",
            messages=roleplay_messages
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

        # 3. SUGGESTED RESPONSES: must directly respond to what the character just said
        suggestions_prompt = (
            f"Scenario: {scenario}. The character just said: \"{clean_text[:300]}\"\n\n"
            "Suggest exactly 4 short phrases a child might say NEXT in direct response to what the character JUST said. "
            "Rules: Each suggestion must stay ON TOPIC with the character's message. "
            "If the character said they love gummy bears, suggest things about gummy bears or agreeing (e.g. 'I love gummy bears too!', 'What's your favorite flavor?')—do NOT suggest unrelated things like cookies or other topics. "
            "If the character is helping the child find someone or something, suggest things that continue that (e.g. 'She was wearing a red shirt', 'Let's look over there'). "
            "One phrase per line, no numbers or bullets. Keep each under 10 words. Only in-context replies."
        )
        try:
            sugg_response = client.chat.complete(
                model="mistral-small-latest",
                messages=[
                    {"role": "system", "content": "Reply with only 4 short phrases that directly respond to the character's last message. One per line. No numbering. Stay on the same topic."},
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
