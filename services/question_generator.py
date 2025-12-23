# Import necessary libraries
import os
import re
import json
import time
import pandas as pd
import google.generativeai as genai
import textstat

from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config.setting import model

# Configuration
QUESTION_TYPE_CSV = "model_training/processed_data/questionType.csv"
WORD_CSV = "model_training/processed_data/ielts_vocab.csv"
TRAINING_CSV = "model_training/processed_data/training_set.csv"
GENERATED_JSON = "model_training/generated_questions/generated_questions.json"
TEMP_CSV = "model_training/generated_questions/temp_generated_questions.json"

MAX_ATTEMPT = 2 
REWARD_GOAL = 4

MAX_API_CALLS_PER_RUN = 10 
API_CALL_COUNT = 0

MIN_DELAY_BETWEEN_CALLS = 13
LAST_API_CALL_TIME = 0

# Load Data
question_type_df = pd.read_csv(QUESTION_TYPE_CSV)
common_vocab_df = pd.read_csv(WORD_CSV)
training_df = pd.read_csv(TRAINING_CSV)

# Prompt Template
PROMPT_TEMPLATE = """
You are an expert IELTS Listening question generator.
Create realistic IELTS Listening questions and transcripts following the official format.

--- QUESTION REQUIREMENTS ---
Section: {section}
Question Type: {typeID} - {type_name}
Question Numbers: {question_range}
Number of Questions: {question_count}

Theme: {theme}
Specific Topic: {specific_topic}
Additional Specifications from Test Creator: {specifications}

Instructions to Display: {instruction}
Expected Answer Format: {answer_format}
Format Rules: {format}
Key Listening Skills: {key_skills}
Typical Duration: {avg_duration}
Expected Transcript Length: {avg_script_length} words
Audio Speed: {audio_speed}
Key Features: {key_features}

--- OUTPUT REQUIREMENTS ---
1. Produce exactly {question_count} questions.
2. Output MUST be valid JSON ONLY, with these keys:
   "Section", "Type", "Instructions", "Diagram",
   "Questions", "Answers", "Options", "Transcript".
3. "Questions" must be a list of strings.
4. "Answers" must be a list of strings of equal length.
5. The type should be T001, T002, T003 and so on only.
6. Question instruction should be the instructions to display and expected answer format.
7. For multiple-choice types, include "Options" (list of lists).
8. The diagram should be drawn in the characters and plain text only. You should handle the space and next line correctly.
9. The maximum width of the diagram is 75 characters including the border line.
9. Transcript MUST naturally reference ALL question numbers in {question_range}.
10. The transcript should include the introduction as the exact IELTS listening test. Do not include other explanations including question numbers and pause. Only the Narrator, People and their conversation.
11. No Markdown. No explanations. JSON ONLY.

Return the JSON format only.
"""

# JSON Parser
def safe_json_parse(raw):
    if not raw: return None
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except:
        return None
    
# Reward Functions
def calculate_readability_score(text):
    return textstat.flesch_reading_ease(str(text))

def is_in_average_word_count(text, section_label):
    if not text: return False
    words = re.findall(r'\b\w+\b', str(text))
    wc = len(words)
    expected = {
        "Section 1": (500, 700),
        "Section 2": (600, 800),
        "Section 3": (800, 1000),
        "Section 4": (1000, 1200)
    }
    low, high = expected.get(section_label, (0, 99999))
    return low <= wc <= high

def calculate_common_word_ratio(text):
    common_vocab = set(common_vocab_df["Words"].str.lower())
    words = [w.lower() for w in re.findall(r'\b\w+\b', str(text))]
    if not words: return 0
    uncommon = [w for w in words if w not in common_vocab]
    return len(uncommon) / len(words)

def calculate_similarity(text):
    existing_texts = []

    # 1. From training_df
    if "transcript" in training_df.columns:
        existing_texts += training_df["transcript"].dropna().astype(str).tolist()

    # 2. From generated JSON
    if os.path.exists(GENERATED_JSON):
        with open(GENERATED_JSON, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

            for item in saved_data:

                # CASE A: item is dict
                if isinstance(item, dict):
                    transcript = item.get("Transcript", "")

                # CASE B: item is string
                elif isinstance(item, str):
                    transcript = item

                # CASE C: item is list
                elif isinstance(item, list):
                    transcript = " ".join(map(str, item))

                # Unknown type
                else:
                    continue

                # Normalise to string
                existing_texts.append(str(transcript))

    # No existing corpus
    if not existing_texts:
        return 0.0

    # Normalise input text
    if isinstance(text, list):
        text = " ".join(map(str, text))
    text = str(text)

    # Build TF-IDF Similarity
    corpus = existing_texts + [text]

    vec = TfidfVectorizer().fit_transform(corpus)
    sims = cosine_similarity(vec[-1], vec[:-1]).flatten()

    return max(sims) if len(sims) else 0.0

# Question number calculation
def get_question_counts(types):
    if len(types) == 1:
        return {types[0]: 10}
    return {types[0]: 5, types[1]: 5}

def number_ranges(counts, section_num):
    start = (section_num - 1) * 10 + 1
    ranges = {}
    cur = start
    for t, c in counts.items():
        ranges[t] = f"{cur}-{cur+c-1}"
        cur += c
    return ranges

def model_generate(prompt, max_retries=3, base_delay=20):
    global API_CALL_COUNT, LAST_API_CALL_TIME

    if API_CALL_COUNT >= MAX_API_CALLS_PER_RUN:
        print("[GEMINI] Local per-run API limit reached, skipping further calls.")
        return None

    current_time = time.time()
    time_since_last_call = current_time - LAST_API_CALL_TIME
    if time_since_last_call < MIN_DELAY_BETWEEN_CALLS:
        wait_time = MIN_DELAY_BETWEEN_CALLS - time_since_last_call
        print(f"[GEMINI] Rate limiting: waiting {wait_time:.1f} seconds before next API call...")
        time.sleep(wait_time)

    for attempt in range(max_retries):
        try:
            LAST_API_CALL_TIME = time.time()
            response = model.generate_content(prompt)
            API_CALL_COUNT += 1
            return safe_json_parse(response.text)
            
        except Exception as e:
            error_str = str(e)
            
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                retry_delay = base_delay
                if "retry in" in error_str.lower():
                    try:
                        import re
                        delay_match = re.search(r'retry in (\d+(?:\.\d+)?)', error_str.lower())
                        if delay_match:
                            retry_delay = float(delay_match.group(1)) + 2
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    print(f"[GEMINI] Rate limit exceeded. Waiting {retry_delay:.1f} seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(retry_delay)
                    base_delay = min(base_delay * 1.5, 60)
                    continue
                else:
                    print(f"[GEMINI] Rate limit exceeded after {max_retries} attempts. Skipping this generation.")
                    return None
            else:
                print(f"[GEMINI] Error during generate_content: {e}")
                return None
    
    return None

def generate_full_set(section_choices):
    global API_CALL_COUNT, LAST_API_CALL_TIME
    API_CALL_COUNT = 0
    LAST_API_CALL_TIME = 0

    all_results = []
    dt_key = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    for part_num_str, part_data in section_choices.get("Part", {}).items():
        # Convert part_num to integer
        part_num = int(part_num_str)
        entries = []

        # Prepare entries for this part
        for i, typeID in enumerate(part_data.get("type1", [])):
            entry = {
                "typeID": typeID,
                "theme": section_choices.get("Themes", [""])[0],
                "topic": part_data.get("topic", [""])[i] if i < len(part_data.get("topic", [])) else "",
                "spec": part_data.get("specifications", [""])[i] if i < len(part_data.get("specifications", [])) else "",
                "number_of_questions": part_data.get("number_of_questions", [0])[i] if i < len(part_data.get("number_of_questions", [])) else 0
            }
            entries.append(entry)

        section_label = f"Part {part_num}"

        # Map typeIDs to counts
        types = [e["typeID"] for e in entries]
        counts = get_question_counts(types)
        ranges = number_ranges(counts, part_num)

        for entry in entries:
            typeID = entry["typeID"]
            theme = entry["theme"]
            topic = entry["topic"]
            spec = entry["spec"]

            # Find type info in question_type_df
            type_row = question_type_df[question_type_df["typeID"] == typeID]
            if type_row.empty:
                print(f" WARNING: typeID '{typeID}' not found. Using placeholder info.")
                type_info = {
                    "type": f"Unknown Type ({typeID})",
                    "instruction": "Follow standard instructions.",
                    "answer_format": "List of answers",
                    "format": "Text",
                    "key_skills": "Listening",
                    "avg_duration": "3-4 min",
                    "avg_script_length": "600",
                    "key_features": "IELTS standard",
                    "audio_speed": "Normal"
                }
            else:
                type_info = type_row.iloc[0]

            q_type_name = type_info["type"]
            question_count = counts.get(typeID, 0)
            question_range = ranges.get(typeID, (1, question_count))

            best_reward = -99
            best_json = None
            rate_limit_hit = False

            for attempt in range(1, MAX_ATTEMPT + 1):
                print(f"\n[GENERATING] {section_label} - {q_type_name} Attempt {attempt}")

                prompt = PROMPT_TEMPLATE.format(
                    section=section_label,
                    question_range=question_range,
                    question_count=question_count,
                    typeID=typeID,
                    type_name=q_type_name,
                    theme=theme,
                    specific_topic=topic,
                    specifications=spec,
                    instruction=type_info.get("instruction", ""),
                    answer_format=type_info.get("answer_format", ""),
                    format=type_info.get("format", ""),
                    key_skills=type_info.get("key_skills", ""),
                    avg_duration=type_info.get("avg_duration", ""),
                    avg_script_length=type_info.get("avg_script_length", ""),
                    key_features=type_info.get("key_features", ""),
                    audio_speed=type_info.get("audio_speed", ""),
                )

                model_json = model_generate(prompt)

                if model_json is None:
                    if API_CALL_COUNT >= MAX_API_CALLS_PER_RUN:
                        print("  API call limit reached, using placeholder")
                        rate_limit_hit = True
                        break
                    continue

                if not isinstance(model_json, dict):
                    print("  Invalid JSON, trying again...")
                    continue

                transcript = model_json.get("Transcript", "")
                reward = 0
                if calculate_readability_score(transcript) >= 55: reward += 1
                if is_in_average_word_count(transcript, section_label): reward += 1
                if calculate_common_word_ratio(transcript) >= 0.1: reward += 1
                if calculate_similarity(transcript) <= 0.85: reward += 1

                print(f" -> Reward: {reward}")

                if reward > best_reward:
                    best_reward = reward
                    best_json = model_json

                if reward == REWARD_GOAL:
                    break
                
                if attempt < MAX_ATTEMPT:
                    time.sleep(10)

            if best_json is None:
                best_json = {
                    "Section": section_label,
                    "Type": q_type_name,
                    "Instructions": type_info.get("instruction", ""),
                    "Diagram": None,
                    "Questions": [f"Placeholder Q{i}" for i in range(1, question_count+1)],
                    "Answers": [f"Answer_{i}" for i in range(1, question_count+1)],
                    "Options": [None]*question_count,
                    "Transcript": f"Placeholder transcript {question_range}"
                }

            all_results.append(best_json)
            
            time.sleep(10)

    wrapped_output = {dt_key: all_results}

    output_dir = os.path.join("static", "temp")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "temp_generated_questions.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(wrapped_output, f, indent=2, ensure_ascii=False)

    print(f"\nFull question set saved to {output_path}")
    return wrapped_output

def generate_specific_part(part_num, new_spec, section_choices):
    global API_CALL_COUNT, LAST_API_CALL_TIME
    API_CALL_COUNT = 0
    LAST_API_CALL_TIME = 0

    dt_key = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    part_num_str = str(part_num)
    
    part_data = section_choices.get("Part", {}).get(part_num_str)
    if not part_data:
        print(f"Error: Part {part_num} configuration not found in section_choices.")
        return None

    types = part_data.get("type1", [])
    counts = get_question_counts(types)
    ranges = number_ranges(counts, int(part_num))
    
    part_results = []
    section_label = f"Part {part_num}"

    for i, typeID in enumerate(types):
        type_row = question_type_df[question_type_df["typeID"] == typeID]
        type_info = type_row.iloc[0] if not type_row.empty else {}
        
        q_type_name = type_info.get("type", "Standard Question")
        question_count = counts.get(typeID, 0)
        question_range = ranges.get(typeID, "")

        best_reward = -99
        best_json = None

        for attempt in range(1, MAX_ATTEMPT + 1):
            print(f"\n[RE-GENERATING] {section_label} - {q_type_name} Attempt {attempt}")
            
            prompt = PROMPT_TEMPLATE.format(
                section=section_label,
                question_range=question_range,
                question_count=question_count,
                typeID=typeID,
                type_name=q_type_name,
                theme=section_choices.get("Themes", [""])[0],
                specific_topic=part_data.get("topic", [""])[i] if i < len(part_data.get("topic", [])) else "",
                specifications=new_spec, # Applied here
                instruction=type_info.get("instruction", ""),
                answer_format=type_info.get("answer_format", ""),
                format=type_info.get("format", ""),
                key_skills=type_info.get("key_skills", ""),
                avg_duration=type_info.get("avg_duration", ""),
                avg_script_length=type_info.get("avg_script_length", ""),
                key_features=type_info.get("key_features", ""),
                audio_speed=type_info.get("audio_speed", ""),
            )

            model_json = model_generate(prompt)

            if isinstance(model_json, dict):
                transcript = model_json.get("Transcript", "")
                reward = 0
                if calculate_readability_score(transcript) >= 55: reward += 1
                if is_in_average_word_count(transcript, section_label): reward += 1
                if calculate_common_word_ratio(transcript) >= 0.1: reward += 1
                if calculate_similarity(transcript) <= 0.85: reward += 1

                if reward > best_reward:
                    best_reward = reward
                    best_json = model_json
                if reward == REWARD_GOAL: break

        part_results.append(best_json if best_json else {"Error": "Failed to generate"})

    temp_path = os.path.join("static", "temp", "temp_generated_questions.json")

    try:
        if os.path.exists(temp_path):
            with open(temp_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            # Get the existing key and list
            if isinstance(existing, dict) and len(existing) > 0:
                existing_key = next(iter(existing.keys()))
                existing_list = existing.get(existing_key, [])
            else:
                existing_key = dt_key
                existing_list = []
        else:
            existing_key = dt_key
            existing_list = []
    except Exception as e:
        print(f"Error reading existing temp file: {e}")
        existing_key = dt_key
        existing_list = []

    # Remove old entries for this part
    new_list = [item for item in existing_list if str(item.get("Section", "")).strip() != section_label]

    # Append new part results
    # If generated items include Section field, ensure it's set
    for item in part_results:
        if isinstance(item, dict):
            item.setdefault("Section", section_label)
        new_list.append(item)

    # Try to sort by numeric part if possible
    def section_sort_key(it):
        s = str(it.get("Section", ""))
        try:
            return int(re.sub(r"[^0-9]", "", s))
        except:
            return 999

    new_list.sort(key=section_sort_key)

    wrapped_output = {existing_key: new_list}

    try:
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(wrapped_output, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing merged temp file: {e}")

    print(f"\nPart {part_num} updated and merged into {temp_path}")
    return wrapped_output
