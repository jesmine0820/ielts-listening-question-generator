# Import necessary libraries
import os
import io
import nltk
import soundfile as sf
import numpy as np

from pydub import AudioSegment
from config.setting import model, tts

nltk.download("punkt")

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
    
def generate_section_audio(transcript_text, section_label):
    voices = {}
    section_audio = AudioSegment.silent(1000)
    
    lines = transcript_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line: continue

        if line.lower().startswith("narrator:"):
            speaker, spoken = "narrator", line.split(":", 1)[1].strip()
            if speaker not in voices: voices[speaker] = narrator_voice()
        elif ":" in line:
            speaker, spoken = line.split(":", 1)
            speaker, spoken = speaker.strip(), spoken.strip()
            if speaker not in voices: voices[speaker] = assign_voice(speaker)
        else:
            speaker, spoken = "unknown", line
            if speaker not in voices: voices[speaker] = narrator_voice()

        audio_np = np.asarray(tts.tts(text=spoken, speaker=voices[speaker], language="en"))
        
        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, audio_np, 22050, format="wav")

        wav_buffer.seek(0)
        section_audio += AudioSegment.from_wav(wav_buffer)
        
        section_audio += AudioSegment.silent(400 if len(spoken.split()) > 18 else 300)

    return section_audio

def save_full_audio(part_audios, output_dir):
    combined = AudioSegment.empty()
    for i, audio in enumerate(part_audios, 1):
        part_path = os.path.join(output_dir, f"part_{i}.wav")
        audio.export(part_path, format="wav")
        
        # Build the combined version
        combined += audio
        combined += AudioSegment.silent(2000)
    
    # Export the full set audio to the set folder with standardized name
    full_audio_path = os.path.join(output_dir, "full_set_audio.wav")
    combined.export(full_audio_path, format="wav")

    return full_audio_path