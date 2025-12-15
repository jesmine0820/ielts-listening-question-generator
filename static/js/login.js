// =============== Import ===============
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.6.0/firebase-app.js";
import { 
    getAuth, 
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    GoogleAuthProvider, 
    signInWithPopup
} from "https://www.gstatic.com/firebasejs/12.6.0/firebase-auth.js";

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
const auth = getAuth(app);

// =============== Modal Configuration ===============
const modalIds = ["signup", "login", "forgot"];
const modals = Object.fromEntries(
    modalIds.map((id) => [id, document.getElementById(`${id}-modal`)])
);

// =============== Configuration ===============
// Sign Up Elements
const signupForm = document.getElementById("signup-form");
const signupGoogle = document.getElementById("signup-google");

// Login Elements
const loginForm = document.getElementById("login-form");
const loginGoogle = document.getElementById("login-google");

// Forgot Password Elements
const forgotForm = document.getElementById("forgot-form");
const emailInput = document.getElementById("forgot-email");
const otpInput = document.getElementById("forgot-otp");
const newPassInput = document.getElementById("forgot-new-password");
const confirmPassInput = document.getElementById("forgot-confirm-password");
const emailGroup = document.getElementById("forgot-email-group");
const otpGroup = document.getElementById("forgot-otp-group");
const newPassGroup = document.getElementById("forgot-new-password-group");
const confirmPassGroup = document.getElementById("forgot-confirm-password-group");
const resendBtn = document.getElementById("resend-otp");
const submitBtn = document.getElementById("forgot-submit");

let step = 1;
let countdown = 60;
let timer = null;

// =============== Modal Navigation ===============
function showModal(name) {
    modalIds.forEach((id) => {
        const modal = modals[id];
        if (!modal) return;
        if (id === name) {
            modal.classList.add("active");
        } else {
            modal.classList.remove("active");
        }
    });

    if (name !== "forgot") {
        resetForgotState();
    }
}

document.querySelectorAll("[data-modal]").forEach((el) => {
    el.addEventListener("click", (e) => {
        e.preventDefault();
        const target = el.getAttribute("data-modal");
        if (target) showModal(target);
    });
});

// =============== Sign Up ===============
signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById("signup-email").value;
    const password = document.getElementById("signup-password").value;
    const confirmPassword = document.getElementById("signup-confirm-password").value;

    // Check password
    if (password !== confirmPassword) {
        alert("Passwords do not match!");
        return;
    }

    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        alert("Account created successfully! Welcome " + userCredential.user.email);
    } catch (error) {
        // Firebase error codes
        if (error.code === 'auth/email-already-in-use') {
            alert("This email is already registered. Please log in instead.");
        } else if (error.code === 'auth/invalid-email') {
            alert("Invalid email address.");
        } else if (error.code === 'auth/weak-password') {
            alert("Password should be at least 6 characters.");
        } else {
            alert(error.message);
        }
    }
});

// Sign up with Google
signupGoogle.addEventListener('click', async () => {
    const provider = new GoogleAuthProvider();
    try {
        const result = await signInWithPopup(auth, provider);
        alert("Welcome " + result.user.email);
    } catch (error) {
        alert(error.message);
    }
});

// =============== Login ===============
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;

    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;

        alert("Login successful! Welcome back " + userCredential.user.email);

        await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                uid: user.uid,
                email: user.email
            })
        });

        window.location.href = "/dashboard";
    } catch (error) {
        // Firebase error codes
        if (error.code === 'auth/user-not-found') {
            alert("No account found with this email.");
        } else if (error.code === 'auth/wrong-password') {
            alert("Incorrect password.");
        } else {
            alert(error.message);
        }
    }
});

// Login with Google
loginGoogle.addEventListener('click', async  () => {
    const provider = new GoogleAuthProvider();
    try {
        const result = await signInWithPopup(auth, provider);
        const user = result.user;

        alert("Welcome " + result.user.displayName);

        await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                uid: user.uid,
                email: user.email
            })
        });

        window.location.href = "/dashboard";

    } catch (error) {
        alert(error.message);
    }
});

// =============== Forgot Password ===============
function resetForgotState() {
    step = 1;

    emailInput.value = "";
    otpInput.value = "";
    newPassInput.value = "";
    confirmPassInput.value = "";

    emailGroup.style.display = "block";
    otpGroup.style.display = "none";
    newPassGroup.style.display = "none";
    confirmPassGroup.style.display = "none";

    emailInput.required = true;
    otpInput.required = false;
    newPassInput.required = false;
    confirmPassInput.required = false;

    submitBtn.textContent = "Send OTP";

    resendBtn.disabled = true;
    resendBtn.textContent = "Resend OTP";

    if (timer) {
        clearInterval(timer);
        timer = null;
    }
}

function startOtpTimer() {
    resendBtn.disabled = true;
    countdown = 60;
    resendBtn.textContent = `Resend OTP (${countdown}s)`;

    timer = setInterval(() => {
        countdown--;
        resendBtn.textContent = `Resend OTP (${countdown}s)`;

        if (countdown <= 0) {
            clearInterval(timer);
            resendBtn.disabled = false;
            resendBtn.textContent = "Resend OTP";
        }
    }, 1000);
}

forgotForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (step === 1) {
        const email = emailInput.value;

        const res = await fetch("/forgot/send-otp", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ email })
        });

        const data = await res.json();
        if (!res.ok) return alert(data.error);

        emailInput.required = true;
        otpInput.required = false;
        emailGroup.style.display = "none";
        otpGroup.style.display = "block";
        submitBtn.textContent = "Verify OTP";

        startOtpTimer(); 
        step = 2;
    }

    else if (step === 2) {
        const email = emailInput.value;
        const otp = otpInput.value;

        const res = await fetch("/forgot/verify-otp", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ email, otp })
        });

        const data = await res.json();
        if (!res.ok) return alert(data.error);

        emailInput.required = false;
        otpInput.required = true;
        otpGroup.style.display = "none";
        newPassGroup.style.display = "block";
        confirmPassGroup.style.display = "block";
        submitBtn.textContent = "Reset Password";
        step = 3;
    }

    else if (step === 3) {
        const email = emailInput.value;
        const password = newPassInput.value;
        const confirm = confirmPassInput.value;

        otpInput.required = false;
        newPassInput.required = true;
        confirmPassInput.required = true;

        if (password !== confirm) {
            return alert("Passwords do not match");
        }

        const res = await fetch("/forgot/reset-password", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();
        if (!res.ok) return alert(data.error);

        alert("Password reset successful!");
        window.location.href = "/";
    }
});

resendBtn.addEventListener("click", async () => {
    const email = emailInput.value;

    resendBtn.disabled = true;

    const res = await fetch("/forgot/send-otp", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ email })
    });

    const data = await res.json();

    if (!res.ok) {
        resendBtn.disabled = false;
        return alert(data.error);
    }

    alert("OTP resent successfully!");
    startOtpTimer();
});
