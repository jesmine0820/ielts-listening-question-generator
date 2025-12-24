import os 
import google.generativeai as genai

from TTS.api import TTS

API_KEY = os.getenv("API_KEY2")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

# Configure API key
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    generation_config={"response_mime_type": "application/json"}
)

model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
tts = TTS(model_name)