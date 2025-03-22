import google.generativeai as genai
import json
import webbrowser
import re

# === CONFIGURE GEMINI API ===
genai.configure(api_key="AIzaSyDWZEOf29bXyyxfsWVUAzmeu8UGF4RJ-b4")
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# === SEND COMMAND TO GEMINI ===
def ask_marvin(user_input):
    prompt = f"""
You are MARVIN, an AI assistant that translates user commands into structured JSON actions.

ONLY return a JSON response. Examples:

User: Open Instagram  
→ {{ "intent": "open_app", "app": "Instagram" }}

User: Play my liked songs on Spotify  
→ {{ "intent": "play_music", "playlist": "liked songs" }}

User: Read my emails  
→ {{ "intent": "read_emails" }}

Now respond to: "{user_input}"
"""

    response = model.generate_content(prompt)
    return response.text

# === EXTRACT JSON FROM RESPONSE ===
def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None

# === HANDLE THE COMMAND ===
def handle_command(command_data):
    intent = command_data.get("intent")

    if intent == "open_app":
        app = command_data.get("app", "").lower()
        if app == "instagram":
            webbrowser.open("https://instagram.com")
        elif app == "youtube":
            webbrowser.open("https://youtube.com")
        elif app == "spotify":
            webbrowser.open("https://open.spotify.com")
        else:
            print(f"Sorry, I don't know how to open {app}.")
    elif intent == "play_music":
        playlist = command_data.get("playlist", "liked songs")
        print(f"Pretending to play your '{playlist}' playlist on Spotify 🎵")
    elif intent == "read_emails":
        print("Pretending to read your emails... ✉️")
    else:
        print("Unknown intent. 🤖")

# === INTERACTION LOOP ===
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    try:
        json_response = ask_marvin(user_input)
        print("MARVIN:", json_response)
        command_data = extract_json(json_response)
        if command_data:
            handle_command(command_data)
        else:
            print("Could not extract valid JSON.")
    except Exception as e:
        print("Error:", e)
