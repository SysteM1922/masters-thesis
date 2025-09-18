from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import random

load_dotenv(".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AUDIO_FOLDER = "audio"

openai = AsyncOpenAI(
    api_key=OPENAI_API_KEY
)

async def text_to_speech(text: str, intent: str):
    """Convert text to speech using OpenAI's TTS model."""
    
    # check if audio/{intent}/ folder exists and has at least 5 files
    if os.path.exists(f"{AUDIO_FOLDER}/{intent}/"):
        if len(os.listdir(f"{AUDIO_FOLDER}/{intent}/")) > 4:
            files = os.listdir(f"{AUDIO_FOLDER}/{intent}/")
            return f"{AUDIO_FOLDER}/{intent}/{random.choice(files)}"
    
    else:
        os.makedirs(f"{AUDIO_FOLDER}/{intent}/", exist_ok=True)

    response = await openai.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text,
        instructions="Speak in European Portuguese",
        response_format="mp3",
    )
    current_audio_folder_size = len(os.listdir(f"{AUDIO_FOLDER}/{intent}/"))
    filename = f"{AUDIO_FOLDER}/{intent}/{intent}_{current_audio_folder_size}.mp3"
    response.write_to_file(filename)
    return filename