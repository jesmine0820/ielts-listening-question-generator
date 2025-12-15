import firebase_admin
from firebase_admin import credentials, auth

# Prevent double initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("config/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

firebase_auth = auth