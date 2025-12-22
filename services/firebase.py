import firebase_admin
from firebase_admin import credentials, auth, firestore, storage

# Prevent double initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("config/serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'final-year-project-96d1e.appspot.com'
    })

firebase_auth = auth

# Firestore client
db = firestore.client()

# Storage bucket
bucket = storage.bucket()

def add_json_to_firestore(collection_name, document_name, data):
    try:
        doc_ref = db.collection(collection_name).document(document_name)
        doc_ref.set(data)
    except Exception as e:
        print(f"An error occurred while adding data to Firestore: {e}")

def get_json_from_firestore(collection_name, document_name):
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

def upload_file_to_storage(file_path, storage_path):
    try:
        blob = bucket.blob(storage_path)
        blob.upload_from_filename(file_path)
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print(f"Error uploading file to Storage: {e}")
        return None