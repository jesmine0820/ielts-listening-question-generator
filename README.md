# fyp-ielts-listening-generator
## Introduction
This is my final year project which titled "IELTS Question Generator for Listening Module By Using LLM (Gemini).

## Description
* User can generate questions with the audios.
* User can download the questions and audios in pdf format and text file.
* User can adjust and customize the theme and specifications.

## Technologies
* Frontend -> HTML, CSS, JavaScript
* Backend -> Flask API
* Model -> Python
* Deployment -> Render

## Training Set Resource
* https://engexam.info/ielts-listening-practice-tests-printable/

## Ways to Run
1. Backend
python -m venv venv 
cd backend
venv\Scripts\activate
pip install -r requirements.txt
python app.py

2. Frontend
cd frontend
npm install
npm start

## Authentication Setup

### Firebase Configuration
1. The Firebase configuration is already set up in `frontend/static/js/app.js`
2. Make sure your Firebase project has Authentication enabled
3. Enable the following sign-in methods in Firebase Console:
   - Email/Password
   - Google
   - Facebook

### Facebook Authentication Setup
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app or use an existing one
3. Add "Facebook Login" product to your app
4. Configure OAuth Redirect URIs in Facebook App Settings:
   - Add: `https://final-year-project-96d1e.firebaseapp.com/__/auth/handler`
5. Copy App ID and App Secret
6. In Firebase Console → Authentication → Sign-in method → Facebook:
   - Enable Facebook
   - Paste App ID and App Secret
   - Save

### Email Configuration (for OTP)
To enable email sending for password reset OTP:

1. **Option 1: Using Gmail SMTP**
   - Set environment variables:
     ```bash
     export SMTP_SERVER=smtp.gmail.com
     export SMTP_PORT=587
     export SMTP_EMAIL=your-email@gmail.com
     export SMTP_PASSWORD=your-app-password
     ```
   - For Gmail, you need to generate an [App Password](https://support.google.com/accounts/answer/185833)

2. **Option 2: Using SendGrid/Mailgun**
   - Update `backend/app.py` to use SendGrid or Mailgun API
   - Install the respective package: `pip install sendgrid` or `pip install mailgun`

3. **Option 3: Firebase Cloud Functions**
   - Deploy a Cloud Function to send emails
   - Use Firebase Extensions for email sending

**Note:** In development mode, if email is not configured, the OTP will be shown in an alert. Remove this in production!

## Features Implemented

### Create Account
- Email/Password registration
- Google Sign-up
- Facebook Sign-up
- Password confirmation validation
- All accounts saved to Firebase Authentication

### Login
- Email/Password authentication
- Google Sign-in
- Facebook Sign-in
- Error handling for invalid credentials

### Forgot Password
- Email-based OTP generation
- OTP verification (6-digit code, expires in 10 minutes)
- New password creation
- Validation: New password cannot be same as old password
- Password update in Firebase