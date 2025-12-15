import { auth, db, googleProvider, facebookProvider } from "./app.js";
import { 
    createUserWithEmailAndPassword, 
    signInWithEmailAndPassword,
    signInWithPopup
} from "https://www.gstatic.com/firebasejs/12.6.0/firebase-auth.js";
import { 
    doc, 
    setDoc, 
    getDoc, 
    deleteDoc,
    serverTimestamp 
} from "https://www.gstatic.com/firebasejs/12.6.0/firebase-firestore.js";

// DOM Elements - Signup
const signupModal = document.getElementById('signup-modal');
const signupForm = document.getElementById('signup-form');
const signupEmailInput = document.getElementById('signup-email');
const signupPasswordInput = document.getElementById('signup-password');
const signupConfirmPasswordInput = document.getElementById('signup-confirm-password');
const signupGoogleButton = document.getElementById('signup-google');
const signupFbButton = document.getElementById('signup-fb');

// DOM Elements - Login
const loginModal = document.getElementById('login-modal');
const loginForm = document.getElementById('login-form');
const loginEmailInput = document.getElementById('login-email');
const loginPasswordInput = document.getElementById('login-password');
const loginGoogleButton = document.getElementById('login-google');
const loginFbButton = document.getElementById('login-fb');

// DOM Elements - Forgot Password
const forgotModal = document.getElementById('forgot-modal');
const forgotForm = document.getElementById('forgot-form');
const forgotEmailInput = document.getElementById('forgot-email');
const forgotOtpInput = document.getElementById('forgot-otp');
const forgotNewPasswordInput = document.getElementById('forgot-new-password');
const forgotConfirmPasswordInput = document.getElementById('forgot-confirm-password');
const forgotSubmitButton = document.getElementById('forgot-submit');
const forgotEmailGroup = document.getElementById('forgot-email-group');
const forgotOtpGroup = document.getElementById('forgot-otp-group');
const forgotNewPasswordGroup = document.getElementById('forgot-new-password-group');
const forgotConfirmPasswordGroup = document.getElementById('forgot-confirm-password-group');

// State for forgot password flow
let forgotPasswordState = 'email';
let forgotPasswordEmail = '';

// Popup modals
function openModal(modal) {
    [signupModal, loginModal, forgotModal].forEach(m => m.classList.remove("active"));
    modal.classList.add("active");
}

// Modal navigation
document.querySelectorAll("a[data-modal]").forEach(link => {
    link.addEventListener("click", e => {
        e.preventDefault();
        const modalName = link.getAttribute("data-modal");
        if (modalName === "login") {
            openModal(loginModal);
        } else if (modalName === "signup") {
            openModal(signupModal);
        } else if (modalName === "forgot") {
            resetForgotPasswordForm();
            openModal(forgotModal);
        }
    });
});

// =============== SIGNUP FUNCTIONALITY ===============

// Signup with Email/Password
signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = signupEmailInput.value.trim();
    const password = signupPasswordInput.value;
    const confirmPassword = signupConfirmPasswordInput.value;

    // Validation
    if (!email || !password || !confirmPassword) {
        alert("Please fill in all fields");
        return;
    }

    if (password !== confirmPassword) {
        alert("Passwords do not match");
        return;
    }

    if (password.length < 6) {
        alert("Password must be at least 6 characters long");
        return;
    }

    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        alert(`Account created successfully! Welcome ${userCredential.user.email}`);
        // Redirect to dashboard or login
        signupForm.reset();
        openModal(loginModal);
    } catch (error) {
        let errorMessage = "An error occurred";
        if (error.code === 'auth/email-already-in-use') {
            errorMessage = "This email is already registered. Please login instead.";
        } else if (error.code === 'auth/invalid-email') {
            errorMessage = "Invalid email address";
        } else if (error.code === 'auth/weak-password') {
            errorMessage = "Password is too weak";
        } else {
            errorMessage = error.message;
        }
        alert(`Error: ${errorMessage}`);
    }
});

// Signup with Google
signupGoogleButton.addEventListener("click", async () => {
    try {
        const result = await signInWithPopup(auth, googleProvider);
        alert(`Account created successfully! Welcome ${result.user.displayName || result.user.email}`);
        // Redirect to dashboard
        window.location.href = 'dashboard.html';
    } catch (error) {
        let errorMessage = "Google sign-up failed";
        if (error.code === 'auth/popup-closed-by-user') {
            errorMessage = "Sign-up cancelled";
        } else {
            errorMessage = error.message;
        }
        alert(errorMessage);
    }
});

// Signup with Facebook
signupFbButton.addEventListener("click", async () => {
    try {
        const result = await signInWithPopup(auth, facebookProvider);
        alert(`Account created successfully! Welcome ${result.user.displayName || result.user.email}`);
        // Redirect to dashboard
        window.location.href = 'dashboard.html';
    } catch (error) {
        let errorMessage = "Facebook sign-up failed";
        if (error.code === 'auth/popup-closed-by-user') {
            errorMessage = "Sign-up cancelled";
        } else if (error.code === 'auth/account-exists-with-different-credential') {
            errorMessage = "An account already exists with this email. Please use a different sign-in method.";
        } else {
            errorMessage = error.message;
        }
        alert(errorMessage);
    }
});

// =============== LOGIN FUNCTIONALITY ===============

// Login with Email/Password
loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = loginEmailInput.value.trim();
    const password = loginPasswordInput.value;

    if (!email || !password) {
        alert("Please enter both email and password");
        return;
    }

    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        alert(`Welcome back, ${userCredential.user.email}!`);
        // Redirect to dashboard
        window.location.href = 'dashboard.html';
    } catch (error) {
        let errorMessage = "Login failed";
        if (error.code === 'auth/user-not-found') {
            errorMessage = "No account found with this email";
        } else if (error.code === 'auth/wrong-password') {
            errorMessage = "Incorrect password";
        } else if (error.code === 'auth/invalid-email') {
            errorMessage = "Invalid email address";
        } else if (error.code === 'auth/invalid-credential') {
            errorMessage = "Invalid email or password";
        } else {
            errorMessage = error.message;
        }
        alert(errorMessage);
    }
});

// Login with Google
loginGoogleButton.addEventListener("click", async () => {
    try {
        const result = await signInWithPopup(auth, googleProvider);
        alert(`Welcome back, ${result.user.displayName || result.user.email}!`);
        // Redirect to dashboard
        window.location.href = 'dashboard.html';
    } catch (error) {
        let errorMessage = "Google sign-in failed";
        if (error.code === 'auth/popup-closed-by-user') {
            errorMessage = "Sign-in cancelled";
        } else {
            errorMessage = error.message;
        }
        alert(errorMessage);
    }
});

// Login with Facebook
loginFbButton.addEventListener("click", async () => {
    try {
        const result = await signInWithPopup(auth, facebookProvider);
        alert(`Welcome back, ${result.user.displayName || result.user.email}!`);
        // Redirect to dashboard
        window.location.href = 'dashboard.html';
    } catch (error) {
        let errorMessage = "Facebook sign-in failed";
        if (error.code === 'auth/popup-closed-by-user') {
            errorMessage = "Sign-in cancelled";
        } else if (error.code === 'auth/account-exists-with-different-credential') {
            errorMessage = "An account already exists with this email. Please use a different sign-in method.";
        } else {
            errorMessage = error.message;
        }
        alert(errorMessage);
    }
});

// =============== FORGOT PASSWORD FUNCTIONALITY ===============

// Generate OTP
function generateOTP() {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

// Store OTP in Firestore
async function storeOTP(email, otp) {
    const otpDoc = {
        email: email,
        otp: otp,
        createdAt: serverTimestamp(),
        expiresAt: new Date(Date.now() + 10 * 60 * 1000) // 10 minutes
    };
    
    await setDoc(doc(db, "passwordResetOTPs", email), otpDoc);
}

// Verify OTP from Firestore
async function verifyOTP(email, otp) {
    try {
        const otpDocRef = doc(db, "passwordResetOTPs", email);
        const otpDocSnap = await getDoc(otpDocRef);
        
        if (!otpDocSnap.exists()) {
            return { valid: false, message: "OTP not found or expired" };
        }
        
        const otpData = otpDocSnap.data();
        const storedOtpValue = otpData.otp;
        const expiresAt = otpData.expiresAt?.toDate();
        
        // Check if OTP is expired
        if (expiresAt && new Date() > expiresAt) {
            await deleteDoc(otpDocRef);
            return { valid: false, message: "OTP has expired. Please request a new one." };
        }
        
        // Verify OTP
        if (storedOtpValue === otp) {
            return { valid: true };
        } else {
            return { valid: false, message: "Invalid OTP" };
        }
    } catch (error) {
        console.error("Error verifying OTP:", error);
        return { valid: false, message: "Error verifying OTP. Please try again." };
    }
}

// Send OTP via backend API (email is sent through Gmail SMTP on the server)
async function sendOTPEmail(email) {
    const response = await fetch('http://localhost:5000/api/send-otp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email })
    });

    const result = await response.json();

    if (result.success) {
        alert(`OTP sent to ${email}. Please check your Gmail inbox (and spam).`);
        return null; // OTP is only in email
    }

    throw new Error(result.error || 'Failed to send OTP');
}

// Get old password hash from Firestore (if stored) or verify via reauthentication
async function getOldPasswordHash(email) {
    // In a real implementation, you might store password hashes
    // For now, we'll verify the new password is different by attempting reauthentication
    // This is a simplified approach - in production, store password hashes securely
    return null;
}

// Reset forgot password form
function resetForgotPasswordForm() {
    forgotPasswordState = 'email';
    forgotPasswordEmail = '';
    storedOtp = '';
    forgotForm.reset();
    forgotEmailGroup.style.display = 'block';
    forgotOtpGroup.style.display = 'none';
    forgotNewPasswordGroup.style.display = 'none';
    forgotConfirmPasswordGroup.style.display = 'none';
    forgotSubmitButton.textContent = 'Send OTP';
}

// Forgot Password Form Handler
forgotForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (forgotPasswordState === 'email') {
        // Step 1: Send OTP
        const email = forgotEmailInput.value.trim();
        
        if (!email) {
            alert("Please enter your email address");
            return;
        }

        try {
            // Send OTP via backend API (email)
            await sendOTPEmail(email);
            
            forgotPasswordEmail = email;
            forgotPasswordState = 'otp';
            
            // Show OTP input field
            forgotEmailGroup.style.display = 'none';
            forgotOtpGroup.style.display = 'block';
            forgotSubmitButton.textContent = 'Verify OTP';
            
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
        
    } else if (forgotPasswordState === 'otp') {
        // Step 2: Verify OTP
        const enteredOtp = forgotOtpInput.value.trim();
        
        if (!enteredOtp || enteredOtp.length !== 6) {
            alert("Please enter a valid 6-digit OTP");
            return;
        }

        try {
            // Verify OTP from Firestore (stored by backend)
            const verification = await verifyOTP(forgotPasswordEmail, enteredOtp);
            
            if (verification.valid) {
                // OTP verified, show new password fields
                forgotPasswordState = 'newpassword';
                forgotOtpGroup.style.display = 'none';
                forgotNewPasswordGroup.style.display = 'block';
                forgotConfirmPasswordGroup.style.display = 'block';
                forgotSubmitButton.textContent = 'Reset Password';
            } else {
                alert(verification.message || "Invalid OTP. Please try again.");
            }
        } catch (error) {
            console.error("OTP verification error:", error);
            alert(`Error: ${error.message || "Failed to verify OTP. Please try again."}`);
        }
        
    } else if (forgotPasswordState === 'newpassword') {
        // Step 3: Update password
        const newPassword = forgotNewPasswordInput.value;
        const confirmPassword = forgotConfirmPasswordInput.value;
        
        if (!newPassword || !confirmPassword) {
            alert("Please fill in all fields");
            return;
        }
        
        if (newPassword !== confirmPassword) {
            alert("Passwords do not match");
            return;
        }
        
        if (newPassword.length < 6) {
            alert("Password must be at least 6 characters long");
            return;
        }

        try {
            // Check if new password is same as old password
            // We'll try to sign in with the new password to check if it's the same
            let isSamePassword = false;
            try {
                await signInWithEmailAndPassword(auth, forgotPasswordEmail, newPassword);
                // If sign in succeeds, the password is the same
                isSamePassword = true;
                // Sign out immediately
                await auth.signOut();
            } catch (signInError) {
                // If sign in fails, password is different (which is what we want)
                isSamePassword = false;
            }
            
            if (isSamePassword) {
                alert("New password cannot be the same as the old password. Please choose a different password.");
                return;
            }
            
            // Call backend API to reset password
            const response = await fetch('http://localhost:5000/api/reset-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: forgotPasswordEmail,
                    otp: forgotOtpInput.value.trim(),
                    newPassword: newPassword
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert("Password reset successfully! Please login with your new password.");
                
                // Clean up OTP from Firestore
                try {
                    await deleteDoc(doc(db, "passwordResetOTPs", forgotPasswordEmail));
                } catch (error) {
                    console.error("Error deleting OTP:", error);
                }
                
                resetForgotPasswordForm();
                openModal(loginModal);
            } else {
                alert(`Error: ${result.error || 'Failed to reset password'}`);
            }
            
        } catch (error) {
            console.error("Password reset error:", error);
            alert(`Error: ${error.message || 'Failed to reset password. Please try again.'}`);
        }
    }
});
