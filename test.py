from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Initialize Firebase Admin SDK
cred_path = os.path.join(os.path.dirname(__file__), 'setting', 'serviceAccountKey.json')
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
        new_password = data.get('newPassword')
        
        if not all([email, otp, new_password]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Verify OTP from Firestore
        otp_doc_ref = db.collection('passwordResetOTPs').document(email)
        otp_doc = otp_doc_ref.get()
        
        if not otp_doc.exists:
            return jsonify({'success': False, 'error': 'OTP not found or expired'}), 400
        
        otp_data = otp_doc.to_dict()
        stored_otp = otp_data.get('otp')
        expires_at = otp_data.get('expiresAt')
        
        # Check if OTP is expired
        if expires_at:
            from datetime import datetime
            # Handle both datetime objects and Firestore timestamps
            if hasattr(expires_at, 'timestamp'):
                expires_datetime = expires_at
            else:
                expires_datetime = expires_at
            if datetime.now() > expires_datetime:
                otp_doc_ref.delete()
                return jsonify({'success': False, 'error': 'OTP has expired'}), 400
        
        # Verify OTP
        if stored_otp != otp:
            return jsonify({'success': False, 'error': 'Invalid OTP'}), 400
        
        # Get user by email
        try:
            user = auth.get_user_by_email(email)
        except Exception as e:
            return jsonify({'success': False, 'error': 'User not found'}), 404
    
        auth.update_user(user.uid, password=new_password)
        
        # Delete OTP after successful password reset
        otp_doc_ref.delete()
        
        return jsonify({'success': True, 'message': 'Password reset successfully'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        # Check if user exists
        try:
            auth.get_user_by_email(email)
        except Exception:
            return jsonify({'success': False, 'error': 'User not found with this email'}), 404
        
        # Generate OTP
        import random
        otp = str(random.randint(100000, 999999))
        
        # Store OTP in Firestore with expiration (10 minutes)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        otp_doc = {
            'email': email,
            'otp': otp,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'expiresAt': expires_at
        }
        db.collection('passwordResetOTPs').document(email).set(otp_doc)
        
        # Gmail SMTP configuration (requires App Password)
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_email = os.getenv('SMTP_EMAIL')
        smtp_password = os.getenv('SMTP_PASSWORD')  # Use App Password
        
        if not smtp_email or not smtp_password:
            return jsonify({'success': False, 'error': 'Email service is not configured on the server'}), 500
        
        try:
            # Build email
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = email
            msg['Subject'] = 'Your OTP Code - IELTS Listening Generator'
            
            body = f"""Hello,

You requested to reset your password for IELTS Listening Generator.

Your OTP code is: {otp}

This code will expire in 10 minutes.

If you did not request this password reset, please ignore this email.

Best regards,
IELTS Listening Generator Team
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email via Gmail
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_email, smtp_password)
                server.send_message(msg)
            
            return jsonify({'success': True, 'message': 'OTP sent to your email'}), 200
        except Exception as e:
            # Cleanup OTP on failure
            db.collection('passwordResetOTPs').document(email).delete()
            return jsonify({'success': False, 'error': f'Failed to send email: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/check-password-same', methods=['POST'])
def check_password_same():
    """
    Check if new password is same as old password
    This requires storing password hashes or using a different approach
    For now, we'll use a simple approach with reauthentication
    """
    try:
        data = request.get_json()
        email = data.get('email')
        new_password = data.get('newPassword')
        
        if not all([email, new_password]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Note: Firebase doesn't allow us to check old password without user being signed in
        # This is a limitation - in production, you might want to:
        # 1. Store password hashes in Firestore (not recommended for security)
        # 2. Require user to enter old password before resetting
        # 3. Use a different authentication flow
        
        # For now, we'll return that we can't check (user should be aware)
        return jsonify({'success': True, 'canCheck': False, 'message': 'Cannot verify if password is same without old password'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

