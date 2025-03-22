import asyncio
import edge_tts

async def speak(text):
    communicate = edge_tts.Communicate(text, voice="en-US-GuyNeural")  # or try "en-US-JennyNeural"
    await communicate.save("output.mp3")

    # Play the result
    import playsound
    playsound.playsound("output.mp3")

asyncio.run(speak("Hey, I’m MARVIN. Ready when you are."))
