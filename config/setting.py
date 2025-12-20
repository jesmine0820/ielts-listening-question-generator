import os 
import google.generativeai as genai

from TTS.api import TTS

API_KEY = "AIzaSyCSC0LPUznCj0USGxAVXjXT_4vgVqp-ah4"
API_KEY2 = "AIzaSyBS-2pbdjYouOkcqHaX4ZI5HHPpSSmq3iw"
API_KEY3 = "AIzaSyDXmaE9QQd0QBHr4konBSr_5qV0O5Q_QuY"
GMAIL_PASSWORD = "etad ijhq fbaa hczn"

# Configure API key
genai.configure(api_key=API_KEY3)
model = genai.GenerativeModel("gemini-2.5-flash")

model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
tts = TTS(model_name)