import os 
import google.generativeai as genai

from TTS.api import TTS

API_KEY = "AIzaSyCJuXFo1dgdDikWruo1uw72PQntB35ikLI"
API_KEY2 = "AIzaSyA30-f8bKwMWj7Bmxw8V4T6wcot1WqSEUs"
API_KEY_AM = "AIzaSyA4rcCCeK3Rp7aB7Fu4EZSHSUgub9CV_Ys"
GMAIL_PASSWORD = "etad ijhq fbaa hczn"

# Configure API key
genai.configure(api_key=API_KEY2)
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    generation_config={"response_mime_type": "application/json"}
)

model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
tts = TTS(model_name)