import google.generativeai as genai
import json
import webbrowser
import re
import sounddevice as sd
import queue
import vosk
import asyncio
import edge_tts
import os
from playsound import playsound
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from fuzzywuzzy import fuzz

# === VOICE SETTINGS ===
VOICE = "en-GB-RyanNeural"  # Current voice
OUTPUT_FILE = "output.mp3"

async def speak_async(text):
    communicate = edge_tts.Communicate(
        text,
        VOICE,
        rate="+30%",  # Faster speech speed
        pitch="-8Hz"  # Deeper tone
    )
    await communicate.save(OUTPUT_FILE)
    playsound(OUTPUT_FILE)
    os.remove(OUTPUT_FILE)

def speak(text):
    print(f"MARVIN (speaking): {text}")
    asyncio.run(speak_async(text))

# === GEMINI SETUP ===
genai.configure(api_key="AIzaSyDWZEOf29bXyyxfsWVUAzmeu8UGF4RJ-b4")  # Your actual API key
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# === VOSK SETUP ===
q = queue.Queue()
model_path = "model/vosk-model-small-en-us-0.15"
vosk_model = vosk.Model(model_path)
samplerate = 16000

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

# === SPOTIFY INTEGRATION ===
client_id = "1ddf1f97075f43e3aee70a0b8786a84e"  # Your Spotify client ID
client_secret = "2bf09d86b9d74d4dbc4b83bd073f2c6b"  # Your Spotify client secret
redirect_uri = "http://localhost:8888/callback"
scope = "user-library-read user-read-playback-state user-modify-playback-state"

# Setup Spotify API connection
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                client_secret=client_secret,
                                                redirect_uri=redirect_uri,
                                                scope=scope))

# === PLAY MUSIC FUNCTION ===
def play_song(song_name):
    result = sp.search(q=song_name, type="track", limit=1)
    if result["tracks"]["items"]:
        song_uri = result["tracks"]["items"][0]["uri"]
        webbrowser.open("https://open.spotify.com")
        print(f"Opening Spotify and playing {song_name}...")
        devices = sp.devices()
        if devices["devices"]:
            sp.start_playback(uris=[song_uri])
            speak(f"Now playing {song_name}.")
            print(f"Playing {song_name}...")
        else:
            speak("No active Spotify device found. Please open Spotify and start playing something first.")
            print("Error: No active Spotify device found.")
    else:
        speak(f"Sorry, I couldn’t find {song_name} on Spotify.")
        print(f"Error: Could not find {song_name}.")

# === GEMINI PROMPT ===
def ask_marvin(user_input):
    prompt = f"""
You are MARVIN, an AI assistant that can interpret user commands in a natural and flexible way.

Return a JSON with:
- "intent": one of ["chat", "open_app", "play_music", "read_emails"]
- "response": what MARVIN should say
- Optional: "app", "song", "playlist"

Examples:

User: "Play Shape of You"  
→ {{
  "intent": "play_music",
  "song": "Shape of You",
  "response": "Now playing Shape of You."
}}

User: "Play a song from my liked songs"  
→ {{
  "intent": "play_music",
  "playlist": "liked songs",
  "response": "Now playing your liked songs."
}}

User: "Can you play anything on Spotify?"  
→ {{
  "intent": "play_music",
  "response": "Now playing something on Spotify."
}}

User: "Open Instagram"  
→ {{
  "intent": "open_app",
  "app": "Instagram",
  "response": "Sure! Opening Instagram."
}}

User: "Hey MARVIN, what's up?"  
→ {{
  "intent": "chat",
  "response": "Not much, just ready to assist you."
}}

Now respond to: "{user_input}"
"""
    response = model.generate_content(prompt)
    return response.text

def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None

# === FUZZY MATCHING FUNCTION ===
def fuzzy_match(command, options):
    max_score = 0
    best_match = ""
    for option in options:
        score = fuzz.ratio(command.lower(), option.lower())
        if score > max_score:
            max_score = score
            best_match = option
    return best_match if max_score > 70 else command  # 70 is the threshold for a valid match

# === HANDLE COMMAND FUNCTION ===
def handle_command(data):
    intent = data.get("intent")
    response = data.get("response", "Okay.")

    speak(response)

    if intent == "open_app":
        app = data.get("app", "").lower()
        urls = {
            "instagram": "https://instagram.com",
            "youtube": "https://youtube.com",
            "spotify": "https://open.spotify.com"
        }
        if app in urls:
            webbrowser.open(urls[app])
        else:
            speak(f"I'm not sure how to open {app}.")
    elif intent == "play_music":
        song_name = data.get("song", "")  # Treat "song" or "playlist" as song name
        if song_name:
            play_song(song_name)  # Call the function to play the song
        else:
            speak("Please provide a song name.")
    elif intent == "read_emails":
        speak("Pretending to read your emails.")
    # else: it was just a chat

# === MAIN LOOP ===
known_commands = [
    "play anything on spotify", "play music", "play a song", "play my liked songs", 
    "play a playlist", "open spotify", "play something", "play my playlist"
]

def listen():
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        rec = vosk.KaldiRecognizer(vosk_model, samplerate)
        print("🎙️ Listening... Speak now.")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                command = result.get("text", "")
                print(f"You said: {command}")
                # Apply fuzzy matching to improve understanding
                command = fuzzy_match(command, known_commands)
                return command

def greet_user():
    speak("Hello. I’m MARVIN, your personal assistant. You can speak to me naturally now.")

greet_user()

while True:
    speak("I'm listening. What would you like me to do?")
    user_input = listen()
    if user_input.lower() in ["exit", "quit", "goodbye"]:
        speak("Goodbye. See you soon.")
        break

    print("You said:", user_input)

    try:
        raw = ask_marvin(user_input)
        print("MARVIN RAW:", raw)
        command_data = extract_json(raw)
        if command_data:
            handle_command(command_data)
        else:
            speak("Hmm, I didn’t quite get that.")
    except Exception as e:
        print("Error:", e)
        speak("There was an error. Please try again.")
