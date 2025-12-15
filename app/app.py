import time
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
)
from flask_cors import CORS
from flask_bcrypt import Bcrypt

# Module
from config.firebase import firebase_auth
from services.gmail import send_otp

app = Flask(__name__)
app.secret_key = "ielts_listening_generator_secret_key"
bcrypt = Bcrypt(app)
CORS(app)

# Login Information Storage
login_activity = {}

# Variable
otp_store = {}

# -- Routes --
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def log_login():
    data = request.get_json()
    uid = data.get('uid')
    email = data.get('email')

    if not uid or not email:
        return jsonify({'error': 'Missing UID or email'}), 400

    login_activity[uid] = {'email': email}
    return jsonify({'message': 'Login recorded successfully'}), 200

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/forgot/send-otp", methods=["POST"])
def send_forgot_otp():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    try:
        firebase_auth.get_user_by_email(email)
    except:
        return jsonify({"error": "Email not found"}), 404
    
    otp = send_otp(email)
    if not otp:
        return jsonify({"error": "Failed to send OTP"}), 500
    
    otp_store[email] = {
        "otp": otp,
        "expires": time.time() + 600
    }

    return jsonify({"message": "OTP sent successfully"}), 200

@app.route("/forgot/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")

    record = otp_store.get(email)
    if not record:
        return jsonify({"error": "OTP not found"}), 400

    if time.time() > record["expires"]:
        return jsonify({"error": "OTP expired"}), 400

    if otp != record["otp"]:
        return jsonify({"error": "Invalid OTP"}), 400

    return jsonify({"message": "OTP verified"}), 200

@app.route("/forgot/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    email = data.get("email")
    new_password = data.get("password")

    if not email or not new_password:
        return jsonify({"error": "Missing data"}), 400

    user = firebase_auth.get_user_by_email(email)

    providers = user.provider_data
    has_password = any(p.provider_id == "password" for p in providers)

    if not has_password:
        return jsonify({
            "error": "This account uses Google Sign-In. Please log in with Google."
        }), 400
    
    auth.update_user(user.uid, password=new_password)

    otp_store.pop(email, None)

    return jsonify({"message": "Password reset successful"}), 200

from firebase_admin import auth

@app.route("/debug/firebase", methods=["GET"])
def debug_firebase():
    users = firebase_auth.list_users().iterate_all()
    emails = [u.email for u in users if u.email]
    return jsonify(emails)

if __name__ == "__main__":
    app.run(debug=True)