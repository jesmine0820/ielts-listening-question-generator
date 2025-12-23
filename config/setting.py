import os 
import google.generativeai as genai

from TTS.api import TTS

API_KEY = "AIzaSyC4FLtet2jdN9lqcsN3QumCcHuYBWp5qcU"
API_KEY2 = "AIzaSyDWtIyEvwBd6Yue1DCEdgXRWzA7TiSj4lU"
API_KEY_AM = "AIzaSyBHbB9NlECSo8bQGOtF-DD_ADtAJEcA4V0"
GMAIL_PASSWORD = "etad ijhq fbaa hczn"

# Configure API key
genai.configure(api_key=API_KEY_AM)
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    generation_config={"response_mime_type": "application/json"}
)

model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
tts = TTS(model_name)