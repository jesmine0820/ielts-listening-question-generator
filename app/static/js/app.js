// =============== Import ===============
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.6.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, FacebookAuthProvider } from "https://www.gstatic.com/firebasejs/12.6.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/12.6.0/firebase-firestore.js";

// =============== Firebase Configuration ===============
const firebaseConfig = {
    apiKey: "AIzaSyDOys-HbHa7kSzgjvmWt603MvD7DSu0Z1c",
    authDomain: "final-year-project-96d1e.firebaseapp.com",
    projectId: "final-year-project-96d1e",
    storageBucket: "final-year-project-96d1e.appspot.com",
    messagingSenderId: "446412928993",
    appId: "1:446412928993:web:d72704b0280dccad1e84a0",
    measurementId: "G-NSSJJ15PRJ"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();
export const facebookProvider = new FacebookAuthProvider();
