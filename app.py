import time
import os
import json
import re
from datetime import datetime
from flask import (
    Flask, Response,
    jsonify, render_template, send_from_directory, stream_with_context,
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
from services.question_generator import generate_full_set, generate_specific_part
from services.convertion import (
    export_full_pdf, 
    export_questions_pdf, 
    export_transcript_txt, 
    export_question_txt
)
from services.audio import generate_section_audio, save_full_audio

app = Flask(__name__)
app.secret_key = "ielts_listening_generator_secret_key"
bcrypt = Bcrypt(app)
CORS(app)

# Storage
login_activity = {}
otp_store = {}

# Ensure folders
TEMP_DIR = os.path.join("model", "temp")
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# ----- Directory Helper -----
def get_latest_set_dir():
    base_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sets')
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        return base_dir
    dirs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) 
            if os.path.isdir(os.path.join(base_dir, d)) and d.startswith("set")]
    if not dirs:
        return base_dir
    return max(dirs, key=os.path.getmtime)

# ----- Templates Routes -----
@app.route("/")
def index(): return render_template("index.html")

@app.route("/dashboard")
def dashboard(): return render_template("dashboard.html")

@app.route("/result")
def result(): return render_template("result.html")

@app.route("/question-generator")
def question_generator(): return render_template("question_generator.html")

# ----- Logic Routes -----

@app.route("/generate", methods=["POST"])
def generate_questions():
    data = request.get_json()
    session['user_choices'] = data 

    # 1. Create unique directory for this specific session
    base_sets_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sets')
    if not os.path.exists(base_sets_dir): os.makedirs(base_sets_dir)
    
    existing = [int(re.search(r"set(\d+)", d).group(1)) for d in os.listdir(base_sets_dir) if re.match(r"set\d+", d)]
    next_set_num = max(existing, default=0) + 1
    target_dir = os.path.join(base_sets_dir, f"set{next_set_num}")
    os.makedirs(target_dir)

    def stream_progress():
        try:
            # PHASE 1: TEXT GENERATION
            yield f"data: {json.dumps({'progress': 15, 'task': 'AI is generating questions...'})}\n\n"
            output = generate_full_set(data)
            dt_key, all_results = next(iter(output.items()))
            
            # PHASE 2: CONVERSION (Passing target_dir to satisfy function arguments)
            yield f"data: {json.dumps({'progress': 35, 'task': 'Creating PDF and Text files...'})}\n\n"
            export_full_pdf(target_dir)
            export_questions_pdf()
            export_transcript_txt()
            export_question_txt()

            # PHASE 3: AUDIO PART BY PART
            part_audios = []
            for i in range(1, 5):
                prog = 35 + (i * 12) 
                yield f"data: {json.dumps({'progress': prog, 'task': f'Converting Part {i} to Audio...'})}\n\n"
                
                # all_results is a list, not a dict. Find items for this part
                part_transcripts = []
                for item in all_results:
                    if isinstance(item, dict) and item.get("Section") == f"Part {i}":
                        transcript = item.get("Transcript", "")
                        if transcript:
                            part_transcripts.append(transcript)
                
                # Combine transcripts if there are multiple question types in this part
                part_text = " ".join(part_transcripts) if part_transcripts else ""
                
                if not part_text:
                    print(f"Warning: No transcript found for Part {i}, using placeholder")
                    part_text = f"Placeholder transcript for Part {i}"
                
                audio_seg = generate_section_audio(part_text, f"Part {i}")
                
                save_path = os.path.join(target_dir, f"part{i}.wav")
                audio_seg.export(save_path, format="wav")
                part_audios.append(audio_seg)

            # PHASE 4: FINAL STITCH
            yield f"data: {json.dumps({'progress': 95, 'task': 'Finalizing full audio set...'})}\n\n"
            save_full_audio(part_audios, os.path.join(target_dir, "full_audio.wav"))
            
            yield f"data: {json.dumps({'progress': 100, 'task': 'Complete!'})}\n\n"
        except Exception as e:
            print(f"Gen Error: {e}")
            yield f"data: {json.dumps({'progress': 0, 'task': f'Error: {str(e)}'})}\n\n"

    return Response(stream_with_context(stream_progress()), mimetype='text/event-stream')

@app.route('/save-to-firebase', methods=['POST'])
def save_to_firebase():
    """Upload 5 files to Firebase Storage and save metadata to Firestore"""
    try:
        data = request.get_json()
        email = data.get('email')
        if not email: return jsonify({"error": "Email is required"}), 400
        
        username = email.split('@')[0]
        latest_dir = get_latest_set_dir()
        
        dt_key = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        document_name = f"{dt_key}_{username}"
        
        # The 5 files to upload (Full set + Questions PDF + 2 TXTs + Full Audio)
        files_to_upload = {
            "full_set.pdf": "full_set.pdf",
            "questions.pdf": "questions.pdf", 
            "transcript.txt": "transcript.txt",
            "questions.txt": "questions.txt",
            "full_audio.wav": "full_audio.wav"
        }
        
        uploaded_urls = {}
        storage_paths = {}
        
        for local_filename, storage_filename in files_to_upload.items():
            file_path = os.path.join(latest_dir, local_filename)
            if not os.path.exists(file_path): continue
            
            storage_path = f"Generated_Questions/{document_name}/{storage_filename}"
            download_url = upload_file_to_storage(file_path, storage_path)
            
            if download_url:
                # Key names in Firestore cannot contain dots, using underscores
                key_name = storage_filename.replace('.', '_')
                uploaded_urls[key_name] = download_url
                storage_paths[key_name] = storage_path
        
        firestore_data = {
            "username": username,
            "email": email,
            "datetime": dt_key,
            "created_at": datetime.now().isoformat(),
            "files": uploaded_urls,
            "storage_paths": storage_paths
        }
        
        add_json_to_firestore("Generated_Questions", document_name, firestore_data)
        
        return jsonify({
            "success": True, 
            "message": "5 files uploaded successfully",
            "document": document_name
        })
    except Exception as e:
        print(f"Firebase Error: {e}")
        return jsonify({"error": str(e)}), 500

# ----- Audio & File Access -----

@app.route('/get_audio/<int:part_num>')
def get_audio(part_num):
    latest_dir = get_latest_set_dir()
    filename = f"part{part_num}.wav"
    return send_from_directory(latest_dir, filename)

@app.route("/get_latest_pdf")
def get_latest_pdf():
    latest_dir = get_latest_set_dir()
    return send_from_directory(latest_dir, "full_set.pdf", mimetype='application/pdf')

@app.route('/download/<file_type>')
def download_file(file_type):
    latest_dir = get_latest_set_dir()
    files = {
        "full": "full_set.pdf", 
        "questions": "questions.pdf", 
        "transcript": "transcript.txt", 
        "audio": "full_audio.wav"
    }
    return send_from_directory(latest_dir, files.get(file_type), as_attachment=True)

@app.route('/regenerate-part', methods=['POST'])
def regen_part():
    data = request.json
    part_num, new_spec = int(data.get('part')), data.get('specification')
    user_choices = session.get('user_choices')
    
    updated_output = generate_specific_part(part_num, new_spec, user_choices)
    
    latest_dir = get_latest_set_dir()
    # Ensure regenerated files go to the correct latest directory
    export_full_pdf(latest_dir)
    export_questions_pdf()
    
    # Extract the part results from the wrapped output
    if updated_output and isinstance(updated_output, dict):
        _, part_results = next(iter(updated_output.items()))
        # part_results is a list, find transcripts for this part
        part_transcripts = []
        for item in part_results:
            if isinstance(item, dict) and item.get("Section") == f"Part {part_num}":
                transcript = item.get("Transcript", "")
                if transcript:
                    part_transcripts.append(transcript)
        
        # Combine transcripts if there are multiple question types
        part_text = " ".join(part_transcripts) if part_transcripts else f"Placeholder transcript for Part {part_num}"
    else:
        part_text = f"Placeholder transcript for Part {part_num}"
    
    new_audio_seg = generate_section_audio(part_text, f"Part {part_num}")
    new_audio_seg.export(os.path.join(latest_dir, f"part{part_num}.wav"), format="wav")
    
    all_audios = [AudioSegment.from_wav(os.path.join(latest_dir, f"part{i}.wav")) for i in range(1, 5)]
    save_full_audio(all_audios, os.path.join(latest_dir, "full_audio.wav"))
    return jsonify({"status": "success"})

# ----- Login & Auth -----

@app.route("/login", methods=["POST"])
def log_login():
    data = request.get_json()
    uid, email = data.get('uid'), data.get('email')
    if not uid or not email: return jsonify({'error': 'Missing data'}), 400
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

@app.route("/api/config")
def get_config():
    return jsonify(get_json_from_firestore("static_data", "ielts_listening_static"))

if __name__ == "__main__":
    app.run(debug=True)