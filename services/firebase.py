import firebase_admin
from firebase_admin import credentials, auth, firestore
import os

# Initialize Firebase only if service account key exists; otherwise operate in local-only mode
firebase_auth = None
db = None

if os.path.exists("config/serviceAccountKey.json"):
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate("config/serviceAccountKey.json")
            # NOTE: storageBucket may be absent in some projects; guard initialization
            firebase_admin.initialize_app(cred, {
                'storageBucket': 'final-year-project-96d1e.appspot.com'
            })
        firebase_auth = auth
        db = firestore.client()
    except Exception as e:
        print(f"Firebase initialization failed: {e}")
        firebase_auth = None
        db = None
else:
    print("Firebase service account not found; running in local-only mode.")

def add_json_to_firestore(collection_name, document_name, data):
    if db is None:
        print("Firestore not initialized; skipping add_json_to_firestore.")
        return
    try:
        import json

        def sanitize(obj):
            try:
                return json.loads(json.dumps(obj, default=str))
            except Exception:
                return str(obj)

        safe_data = sanitize(data)

        doc_ref = db.collection(collection_name).document(document_name)
        doc_ref.set(safe_data)
    except Exception as e:
        print(f"An error occurred while adding data to Firestore: {e}")

def get_json_from_firestore(collection_name, document_name):
    if db is None:
        print("Firestore not initialized; get_json_from_firestore returning empty dict.")
        return {}
    try:
        doc_ref = db.collection(collection_name).document(document_name)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            print(f"Document '{document_name}' does not exist in collection '{collection_name}'.")
            return {}
    except Exception as e:
        print(f"Error retrieving document: {e}")
        return {}
