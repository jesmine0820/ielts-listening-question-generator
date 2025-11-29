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