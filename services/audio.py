# Import necessary libraries
import os
import io
import nltk
import google.generativeai as genai
import soundfile as sf
import numpy as np

from TTS.api import TTS
from pydub import AudioSegment
from IPython.display import Audio

nltk.download("punkt")

# Initialize Coqui-TTS
model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
tts = TTS(model_name)

# Determine Speaker
all_speakers = tts.speakers

male_speakers = [s for s in all_speakers if any(n in s.lower() for n in [
    "david","andrew","badr","damien","gilberto","ilkin","kazuhiko",
    "ludvig","torcull","viktor","zacharie","xavier","luis","marcos"
])]

female_speakers = [s for s in all_speakers if any(n in s.lower() for n in [
    "claribel","daisy","tammie","alison","ana","annmarie","asya","brenda",
    "gitta","henriette","sofia","tammy","tanja","nova","maja","uta",
    "lidiya","chandra","szofi","camilla","lilya","zofija"
])]

male_index = 0
female_index = 0

# Utility Function
def detect_gender(name):
    try:
        r = model.generate_content(
            f"Determine gender (male or female). Name: {name}. Answer only male or female."
        )
        t = r.text.lower()
        if "male" in t: return "male"
        if "female" in t: return "female"
    except:
        pass
    return None

def narrator_voice():
    for s in female_speakers:
        if "daisy" in s.lower():
            return s
    return female_speakers[0]

def assign_voice(name):

    global male_index, female_index
    gender = detect_gender(name)

    if gender == "male":
        v = male_speakers[male_index % len(male_speakers)]
        male_index += 1
        return v

    elif gender == "female":
        v = female_speakers[female_index % len(female_speakers)]
        female_index += 1
        return v

    if male_index <= female_index:
        v = male_speakers[male_index % len(male_speakers)]
        male_index += 1
        return v
    else:
        v = female_speakers[female_index % len(female_speakers)]
        female_index += 1
        return v
    
def create_audio(file_path):

    folder = os.path.dirname(file_path)
    final_path = os.path.join(folder, "audio.wav")
    os.makedirs(folder, exist_ok=True)

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    lines = lines[3:]
    voices = {}
    final_audio = AudioSegment.silent(1500)

    current_line = 0
    total_line = len(lines)

    for raw_line in lines:
        current_line += 1

        line = raw_line.strip()
        if not line:
            continue

        if line.lower().startswith("section"):
            final_audio += AudioSegment.silent(1500)
            continue

        if line.lower().startswith("narrator:"):
            spoken = line.split(":", 1)[1].strip()
            speaker = "narrator"
            voices[speaker] = narrator_voice()

        else:
            if ":" in line:
                speaker, spoken = line.split(":", 1)
                speaker = speaker.strip()
                spoken = spoken.strip()
            else:
                speaker = "unknown"
                spoken = line

            if speaker not in voices:
                voices[speaker] = narrator_voice() if speaker == "unknown" else assign_voice(speaker)

        print(f"Converting -> {current_line} / {total_line}")

        audio_np = np.asarray(
            tts.tts(
                text=spoken,
                speaker=voices[speaker],
                language="en"
            )
        )

        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, audio_np, 22050, format="wav")
        wav_buffer.seek(0)
        audio_seg = AudioSegment.from_wav(wav_buffer)

        final_audio += audio_seg

        final_audio += AudioSegment.silent(300)

        if len(spoken.split()) > 18:
            final_audio += AudioSegment.silent(400)

    final_audio.export(final_path, format="wav")