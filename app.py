import time
import os
import json
import threading
import glob
from datetime import datetime
from flask import (
    Flask, Response,
    jsonify, render_template, stream_with_context, send_from_directory,
    request, session
)
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from pydub import AudioSegment

# Modules
from services.firebase import (
    firebase_auth, 
    get_json_from_firestore,
    upload_file_to_storage,
    add_json_to_firestore
)
from services.gmail import send_otp
from services.question_generator import (
    generate_full_set, 
    generate_specific_part
)
from services.convertion import generate_files
from services.audio import (
    generate_section_audio, 
    save_full_audio
)

# Initialize App
app = Flask(__name__)
app.secret_key = "ielts_listening_generator_secret_key"
bcrypt = Bcrypt(app)
CORS(app)

# Storage
login_activity = {}
otp_store = {}
audio_tasks = {}

AUDIO_TEMP_DIR = os.path.join("static", "generated_audio")
os.makedirs(AUDIO_TEMP_DIR, exist_ok=True)

# ----- Templates Routes -----
@app.route("/")
def index(): 
    return render_template("index.html")

@app.route("/dashboard")
def dashboard(): 
    return render_template("dashboard.html")

@app.route("/question-generator")
def question_generator(): 
    return render_template("question_generator.html")

@app.route("/result")
def result(): 
    return render_template("result.html")

@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/automated-marking")
def automated_marking():
    return render_template("automated_marking.html")

# ----- Utility Function -----
def get_latest_set_folder():
    """Helper to find the set folder with the highest number."""
    base_path = os.path.join("model", "output")
    if not os.path.exists(base_path):
        return None
    
    folders = [f for f in os.listdir(base_path) if f.startswith("set")]
    if not folders:
        return None
    
    folders.sort(key=lambda x: int(x.replace("set", "")))
    return os.path.join(base_path, folders[-1])

# ----- Login & Auth -----
@app.route("/login", methods=["POST"])
def log_login():
    data = request.get_json()
    uid, email = data.get('uid'), data.get('email')
    if not uid or not email: 
        return jsonify({'error': 'Missing data'}), 400
    
    session['user_id'] = uid
    session['email'] = email
    
    login_activity[uid] = {'email': email}
    return jsonify({'message': 'Login recorded'}), 200

@app.route("/forgot/send-otp", methods=["POST"])
def send_forgot_otp():
    data = request.get_json()
    email = data.get("email")
    try:
        firebase_auth.get_user_by_email(email)
        otp = send_otp(email)
        otp_store[email] = {"otp": otp, "expires": time.time() + 600}
        return jsonify({"message": "OTP sent"}), 200
    except:
        return jsonify({"error": "Email not found"}), 404

@app.route("/forgot/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email, otp = data.get("email"), data.get("otp")
    record = otp_store.get(email)
    if record and record["otp"] == otp and time.time() < record["expires"]:
        return jsonify({"message": "Verified"}), 200
    return jsonify({"error": "Invalid or expired OTP"}), 400

@app.route("/forgot/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    email, new_pw = data.get("email"), data.get("password")
    user = firebase_auth.get_user_by_email(email)
    firebase_auth.update_user(user.uid, password=new_pw)
    otp_store.pop(email, None)
    return jsonify({"message": "Reset successful"}), 200

# ----- Question Generator -----
@app.route("/api/config")
def get_config():
    return jsonify(get_json_from_firestore("static_data", "ielts_listening_static"))

@app.route("/api/generate-questions", methods=["POST"])
def api_generate_questions():
    user_input = request.json
    generate_with_audio = user_input.get("generateWithAudio", False)
    
    section_choices = {
        "Themes": user_input.get("Themes", user_input.get("themes", ["General"])),
        "Part": {}
    }

    for i in range(1, 5):
        p_key = str(i)
        part_data = user_input.get("Part", {}).get(p_key, {})
        
        section_choices["Part"][p_key] = {
            "type1": part_data.get("type1", []),
            "topic": part_data.get("topic", []),
            "specifications": part_data.get("specifications", []),
            "number_of_questions": part_data.get("number_of_questions", [])
        }

    def generate_stream():
        try:
            yield f"data: {json.dumps({'progress': 10, 'status': 'Initializing', 'task': 'Formatting request...'})}\n\n"
            
            yield f"data: {json.dumps({'progress': 20, 'status': 'Generating Questions', 'task': 'Calling AI model...'})}\n\n"
            
            full_set_output = generate_full_set(section_choices)
            
            if not full_set_output or len(full_set_output) == 0:
                raise Exception("No questions were generated. Please check your input and try again.")
            
            timestamp_key = list(full_set_output.keys())[0]
            questions_list = full_set_output[timestamp_key]
            
            if not questions_list or len(questions_list) == 0:
                raise Exception("Generated questions list is empty. Please try again.")
            
            session['generated_questions'] = questions_list
            session['section_choices'] = section_choices
            
            yield f"data: {json.dumps({'progress': 50, 'status': 'Questions Generated', 'task': f'Generated {len(questions_list)} question sets'})}\n\n"

            target_set_folder = generate_files()

            if generate_with_audio:
                yield f"data: {json.dumps({'progress': 60, 'status': 'Generating Audio', 'task': 'Synthesizing voices...'})}\n\n"
                
                part_audios = []
                parts_dict = {}
                for item in questions_list:
                    section = item.get("Section", "")
                    try:
                        part_num = int(section.replace("Part", "").strip())
                        if part_num not in parts_dict:
                            parts_dict[part_num] = []
                        parts_dict[part_num].append(item)
                    except:
                        part_num = len(parts_dict) + 1
                        if part_num not in parts_dict:
                            parts_dict[part_num] = []
                        parts_dict[part_num].append(item)
                
                for part_num in range(1, 5):
                    yield f"data: {json.dumps({'progress': 60 + (part_num * 8), 'task': f'Processing Part {part_num} audio...'})}\n\n"
                    
                    transcript = ""
                    if part_num in parts_dict:
                        for item in parts_dict[part_num]:
                            item_transcript = item.get("Transcript", "")
                            if item_transcript:
                                transcript += item_transcript + "\n\n"
                    
                    if transcript:
                        audio_seg = generate_section_audio(transcript, f"Part {part_num}")
                    else:
                        audio_seg = AudioSegment.silent(1000)
                    
                    temp_part_path = os.path.join(AUDIO_TEMP_DIR, f"part_{part_num}.wav")
                    audio_seg.export(temp_part_path, format="wav")
                    
                    part_audios.append(audio_seg)
                
                if part_audios:
                    save_full_audio(part_audios, target_set_folder)

            yield f"data: {json.dumps({'progress': 100, 'success': True, 'status': 'Completed', 'task': 'Material ready!'})}\n\n"

        except Exception as e:
            print(f"Error: {e}")
            yield f"data: {json.dumps({'progress': 0, 'error': str(e)})}\n\n"

    return Response(stream_with_context(generate_stream()), mimetype='text/event-stream')

@app.route("/api/regenerate-part", methods=["POST"])
def regenerate_part():
    data = request.json
    part_num = data.get("part")
    new_spec = data.get("spec")
    
    section_choices = session.get('section_choices')
    
    updated_part_wrapper = generate_specific_part(part_num, new_spec, section_choices)
    
    timestamp_key = list(updated_part_wrapper.keys())[0]
    updated_json = updated_part_wrapper[timestamp_key][0]
    
    audio_seg = generate_section_audio(updated_json.get("Transcript", ""), f"Part {part_num}")
    audio_seg.export(os.path.join(AUDIO_TEMP_DIR, f"part_{part_num}.wav"), format="wav")
    
    return jsonify({"success": True, "updated_data": updated_json})

@app.route("/api/generate-audio-background", methods=["POST"])
def api_audio_background():
    task_id = datetime.now().strftime("%H%M%S")
    audio_tasks[task_id] = "processing"
    
    generated_questions = session.get('generated_questions')
    
    if not generated_questions:
        try:
            import json
            temp_path = os.path.join("model", "temp", "temp_generated_questions.json")
            if os.path.exists(temp_path):
                with open(temp_path, "r", encoding="utf-8") as f:
                    temp_data = json.load(f)
                    timestamp_key = list(temp_data.keys())[0]
                    generated_questions = temp_data[timestamp_key]
                    session['generated_questions'] = generated_questions
        except Exception as e:
            print(f"Error loading questions from temp file: {e}")
            return jsonify({"error": "No generated questions found"}), 400
    
    if not generated_questions:
        return jsonify({"error": "No generated questions found"}), 400

    def run_background_tts(questions, tid):
        try:
            part_audios = []
            parts_dict = {}
            for item in questions:
                section = item.get("Section", "")
                try:
                    part_num = int(section.replace("Part", "").strip())
                    if part_num not in parts_dict:
                        parts_dict[part_num] = []
                    parts_dict[part_num].append(item)
                except:
                    part_num = len(parts_dict) + 1
                    if part_num not in parts_dict:
                        parts_dict[part_num] = []
                    parts_dict[part_num].append(item)
            
            for part_num in range(1, 5):
                transcript = ""
                if part_num in parts_dict:
                    for item in parts_dict[part_num]:
                        item_transcript = item.get("Transcript", "")
                        if item_transcript:
                            transcript += item_transcript + "\n\n"
                
                if transcript:
                    audio_seg = generate_section_audio(transcript, f"Part {part_num}")
                    part_file = os.path.join(AUDIO_TEMP_DIR, f"part_{part_num}.wav")
                    audio_seg.export(part_file, format="wav")
                    part_audios.append(audio_seg)
                else:
                    silent_audio = AudioSegment.silent(1000)
                    part_file = os.path.join(AUDIO_TEMP_DIR, f"part_{part_num}.wav")
                    silent_audio.export(part_file, format="wav")
                    part_audios.append(silent_audio)
            
            if part_audios:
                save_full_audio(part_audios, os.path.join(AUDIO_TEMP_DIR, "full_audio.wav"))
            audio_tasks[tid] = "completed"
        except Exception as e:
            import traceback
            print(f"Background Audio Error: {e}")
            traceback.print_exc()
            audio_tasks[tid] = f"error: {str(e)}"

    # Start the thread
    thread = threading.Thread(target=run_background_tts, args=(generated_questions, task_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({"task_id": task_id})

@app.route("/generate_pdf_preview")
def generate_pdf_preview():
    directory = os.path.join("model/temp")
    return send_from_directory(directory, "full_set.pdf")

@app.route("/api/check-audio-status/<task_id>")
def check_audio_status(task_id):
    status = audio_tasks.get(task_id, "not_found")
    return jsonify({"status": status})

@app.route("/get_audio/<int:part_num>")
def get_audio(part_num):
    return send_from_directory(AUDIO_TEMP_DIR, f"part_{part_num}.wav")

@app.route("/api/save-to-firebase", methods=["POST"]) # Changed 'method' to 'methods'
def save_to_firebase():
    try:
        data = request.json
        selected_filenames = data.get("files", [])
        
        # 1. Get User ID from session
        uid = session.get("user_id")
        if not uid:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        # 2. Find the latest set folder dynamically
        current_set_path = get_latest_set_folder()

        if not current_set_path or not os.path.exists(current_set_path):
            return jsonify({"success": False, "error": "No output folders found in model/output."}), 400

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        folder_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        uploaded_urls = {}

        # 3. Upload each selected file
        for filename in selected_filenames:
            # Match the filenames exactly as they are in the directory
            local_file_path = os.path.join(current_set_path, filename)
            
            # Case-insensitive check just in case
            if not os.path.exists(local_file_path):
                # Try lowercase if exact match fails
                local_file_path = os.path.join(current_set_path, filename.lower())

            if os.path.exists(local_file_path):
                storage_path = f"users/{uid}/{folder_id}/{filename}"
                public_url = upload_file_to_storage(local_file_path, storage_path)
                
                if public_url:
                    # Firestore keys can't have dots, replace with underscore
                    safe_key = filename.replace(".", "_")
                    uploaded_urls[safe_key] = public_url

        if not uploaded_urls:
            return jsonify({"success": False, "error": "No files were successfully uploaded."}), 400

        # 4. Save Record to Firestore
        history_entry = {
            "uid": uid,
            "timestamp": timestamp,
            "folder_name": os.path.basename(current_set_path),
            "files": uploaded_urls
        }
        
        doc_id = f"{uid}_{folder_id}"
        add_json_to_firestore("history", doc_id, history_entry)

        return jsonify({"success": True, "urls": uploaded_urls})

    except Exception as e:
        print(f"Save to Firebase Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ----- History -----
@app.route("/api/get-history")
def get_user_history():
    uid = session.get("user_id") # Ensure you set this at login
    if not uid:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Query Firestore for documents belonging to this UID
        history_ref = db.collection("history")
        query = history_ref.where("uid", "==", uid).order_by("timestamp", direction="DESCENDING")
        docs = query.stream()

        history_list = []
        for doc in docs:
            data = doc.to_dict()
            # data contains: {timestamp, folder_name, files: {filename_ext: url}}
            history_list.append(data)

        return jsonify({"success": True, "history": history_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Main
if __name__ == "__main__":
    app.run(debug=True)