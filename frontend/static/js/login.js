import { auth, provider } from "./app.js";
import { createUserWithEmailAndPassword, signInWithPopup } 
    from "https://www.gstatic.com/firebasejs/12.6.0/firebase-auth.js";

// DOM
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const submitButton = document.getElementById('submit');
const googleButton = document.getElementById('google');

// Create account
submitButton.addEventListener("click", (event) => {
    event.preventDefault();

    const email = emailInput.value;
    const password = passwordInput.value;

    if (!email || !password) {
        alert("Please enter both email and password");
        return;
    }

    createUserWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            alert(`Account created successfully! Welcome ${userCredential.user.email}`);
        })
        .catch((error) => {
            alert(`Error (${error.code}): ${error.message}`);
        });
});

// Google login
googleButton.addEventListener("click", () => {
    signInWithPopup(auth, provider)
        .then((result) => {
            alert(`Signed in as ${result.user.displayName} (${result.user.email})`);
        })
        .catch((error) => {
            alert("Google sign-in failed: " + error.message);
        });
});
