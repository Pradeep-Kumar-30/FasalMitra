// auth.js — FasalMitra local account authentication and legacy admin helpers

// ─────────────────────────────────────────────
// Role constants — single source of truth
// ─────────────────────────────────────────────
export const ROLES = {
  FARMER: "farmer",
  BUYER: "buyer",
  EQUIPMENT: "equipment",
  GROCERY: "grocery",
  EXPERT: "expert",
  ADMIN: "admin",
};

const AUTH_API_BASE = `${window.location.protocol}//${window.location.hostname}:5000/api/auth`;

// Pages each role is allowed to access (filename without path)
const ROLE_HOME = {
  farmer: "farmer.html",
  buyer: "buyer.html",
  equipment: "equipment.html",
  grocery: "grocery.html",
  expert: "expert.html",
  admin: "admin.html",
};

// ─────────────────────────────────────────────
// Firebase remains lazy-loaded for legacy admin profile helpers.
// ─────────────────────────────────────────────
let _app, _db, _firestoreSdk;

async function getFirebaseInstances() {
  if (_db) return { db: _db, firestoreSdk: _firestoreSdk };

  const [appSdk, firestoreSdk] = await Promise.all([
    import("https://www.gstatic.com/firebasejs/10.11.0/firebase-app.js"),
    import("https://www.gstatic.com/firebasejs/10.11.0/firebase-firestore.js"),
  ]);
  const res = await fetch('http://localhost:5000/api/firebase-config');
  if (!res.ok) throw new Error('Failed to fetch Firebase config');
  
  const config = await res.json();

  _app = appSdk.initializeApp(config);
  _db = firestoreSdk.getFirestore(_app);
  _firestoreSdk = firestoreSdk;
  window._agriDb = _db;
  return { db: _db, firestoreSdk };
}

class AuthManager {
  constructor() {
    this.currentUser = null;
  }

  // ── Register ──────────────────────────────
  async register({ role, fullname, email, password }) {
    const validation = this._validateRegistrationData({ role, fullname, email, password });
    if (!validation.valid) {
      return { success: false, message: validation.message };
    }

    const pwCheck = this._validatePassword(password);
    if (!pwCheck.valid) return { success: false, message: pwCheck.message };

    const normalizedEmail = email.trim().toLowerCase();
    const normalizedFullname = fullname.trim();
    const normalizedRole = role.trim().toLowerCase();
    const username = this._createUsername(normalizedEmail);
    const result = await this._requestAuth("register", {
      username,
      email: normalizedEmail,
      password,
      full_name: normalizedFullname,
      role: normalizedRole,
    });

    if (!result.success) return result;

    const loginResult = await this.login(normalizedEmail, password);
    if (loginResult.success) {
      return { ...loginResult, message: "Account created successfully!" };
    }

    return {
      success: true,
      authenticated: false,
      message: "Account created. Please sign in to continue.",
      user: { email: normalizedEmail, fullname: normalizedFullname, role: normalizedRole },
    };
  }

  // ── Login ─────────────────────────────────
  async login(email, password) {
    const validation = this._validateLoginData(email, password);
    if (!validation.valid) {
      return { success: false, message: validation.message };
    }

    const normalizedEmail = email.trim().toLowerCase();
    const result = await this._requestAuth("login", {
      username: normalizedEmail,
      password,
    });

    if (!result.success) return result;

    const data = result.data;
    if (!data.user || !data.access_token) {
      return { success: false, message: "The account service returned incomplete login data." };
    }

    const userData = {
      id: data.user.id,
      fullname: data.user.full_name || data.user.fullname,
      email: data.user.email,
      role: data.user.role,
    };
    this._setSession(userData, data.access_token);

    return { success: true, message: data.message || "Login successful!", user: userData };
  }

  // ── Logout ────────────────────────────────
  async logout() {
    const token = localStorage.getItem("token");
    if (token) {
      const result = await this._requestAuth("logout", {}, token);
      if (!result.success) console.error("Backend logout failed:", result.message);
    }

    sessionStorage.removeItem("agritech_session");
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    this.currentUser = null;
    window.location.href = "login.html";
    return { success: true };
  }

  // ── Check login state ─────────────────────
  isLoggedIn() {
    return this.currentUser !== null;
  }

  // ── Get current user ──────────────────────
  getCurrentUser() {
    if (this.currentUser) return this.currentUser;
    try {
      const s = sessionStorage.getItem("agritech_session");
      if (s) {
        this.currentUser = JSON.parse(s);
        return this.currentUser;
      }
    } catch (_) {}
    return null;
  }

  // ── Role helpers ──────────────────────────
  getHomePageForRole(role) {
    return ROLE_HOME[role] || "main.html";
  }

  // ── Admin: get all users ──────────────────
  async getAllUsers() {
    const { db, firestoreSdk } = await getFirebaseInstances();
    const snap = await firestoreSdk.getDocs(firestoreSdk.collection(db, "users"));
    return snap.docs.map((d) => ({ id: d.id, ...d.data() }));
  }

  // ── Admin: ban / unban ────────────────────
  async setBanned(uid, isBanned) {
    const { db, firestoreSdk } = await getFirebaseInstances();
    await firestoreSdk.updateDoc(firestoreSdk.doc(db, "users", uid), { isBanned });
    return { success: true };
  }

  // ── Admin: change role ────────────────────
  async setRole(uid, newRole) {
    const { db, firestoreSdk } = await getFirebaseInstances();
    await firestoreSdk.updateDoc(firestoreSdk.doc(db, "users", uid), { role: newRole });
    return { success: true };
  }

  // ─────────────────────────────────────────
  // Private helpers
  // ─────────────────────────────────────────
  async _requestAuth(endpoint, payload, token) {
    const headers = { "Content-Type": "application/json" };
    if (token) headers.Authorization = `Bearer ${token}`;

    let response;
    try {
      response = await fetch(`${AUTH_API_BASE}/${endpoint}`, {
        method: "POST",
        headers,
        credentials: "include",
        body: JSON.stringify(payload),
      });
    } catch (error) {
      console.error("Authentication API request failed:", error);
      return {
        success: false,
        message: "Cannot reach the local account service. Start the Flask backend on port 5000 and try again.",
      };
    }

    let data;
    try {
      data = await response.json();
    } catch (error) {
      console.error("Authentication API returned invalid JSON:", error);
      return { success: false, message: "The account service returned an invalid response." };
    }

    if (!response.ok || data.status !== "success") {
      return {
        success: false,
        message: data.message || `Account request failed (${response.status}).`,
      };
    }

    return { success: true, data };
  }

  _createUsername(email) {
    const localPart = email
      .split("@")[0]
      .toLowerCase()
      .replace(/[^a-z0-9._-]/g, "_")
      .slice(0, 20);
    const suffix = crypto.randomUUID().replace(/-/g, "").slice(0, 8);
    return `${localPart || "user"}_${suffix}`;
  }

  _setSession(user, token) {
    this.currentUser = user;
    sessionStorage.setItem("agritech_session", JSON.stringify(user));
    localStorage.setItem("user", JSON.stringify(user));
    localStorage.setItem("token", token);
  }

  _validateEmail(email) {
    return /^[^\s@]+@gmail\.com$/.test(email);
  }

  _validatePassword(password) {
    if (password.length < 8)
      return {
        valid: false,
        message: "Password must be at least 8 characters long",
      };
    if (!/[a-z]/.test(password))
      return {
        valid: false,
        message: "Password must contain at least one lowercase letter",
      };
    if (!/[A-Z]/.test(password))
      return {
        valid: false,
        message: "Password must contain at least one uppercase letter",
      };
    if (!/\d/.test(password))
      return {
        valid: false,
        message: "Password must contain at least one number",
      };
    return { valid: true };
  }

  _validateRegistrationData({ role, fullname, email, password }) {
    if (!role || !fullname || !email || !password) {
      return { valid: false, message: "All fields are required" };
    }

    const normalizedRole = role.trim().toLowerCase();
    const allowedRoles = ["buyer", "farmer", "equipment", "grocery", "expert"];

    if (!allowedRoles.includes(normalizedRole)) {
      return { valid: false, message: "Please select a valid role" };
    }

    if (!/^[a-zA-Z\s.'-]+$/.test(fullname.trim())) {
      return { valid: false, message: "Full name can only contain letters and spaces" };
    }

    if (!this._validateEmail(email)) {
      return { valid: false, message: "Please use a valid @gmail.com address" };
    }

    return { valid: true };
  }

  _validateLoginData(email, password) {
    if (!email || !password) {
      return { valid: false, message: "Email and password are required" };
    }

    if (!this._validateEmail(email)) {
      return { valid: false, message: "Please enter a valid @gmail.com address" };
    }

    return { valid: true };
  }

  // ── UI helper (kept from old auth.js) ─────
  updateAuthUI() {
    const user = this.getCurrentUser();
    const isLoggedIn = !!user;

    const loginBtn = document.querySelector(".login-btn-desktop");
    const registerBtn = document.querySelector(".register-btn-desktop");
    const logoutBtn = document.querySelector(".logout-button");
    const mobileLogin = document.querySelector(
      'a[href="login.html"].mobile-link',
    );
    const mobileReg = document.querySelector(
      'a[href="register.html"].mobile-link',
    );

    if (isLoggedIn) {
      if (loginBtn) loginBtn.style.display = "none";
      if (registerBtn) registerBtn.style.display = "none";
      if (logoutBtn) {
        logoutBtn.style.display = "inline-flex";
        logoutBtn.onclick = (e) => {
          e.preventDefault();
          this.logout();
        };
      }
      if (mobileLogin) mobileLogin.style.display = "none";
      if (mobileReg) mobileReg.style.display = "none";
    } else {
      if (loginBtn) loginBtn.style.display = "inline-flex";
      if (registerBtn) registerBtn.style.display = "inline-flex";
      if (logoutBtn) logoutBtn.style.display = "none";
      if (mobileLogin) mobileLogin.style.display = "flex";
      if (mobileReg) mobileReg.style.display = "flex";
    }
  }
}

// ─────────────────────────────────────────────
// Singleton
// ─────────────────────────────────────────────
window.authManager = new AuthManager();

// ─────────────────────────────────────────────
// Page guards — same function names as before
// ─────────────────────────────────────────────

/**
 * requireAuth([allowedRoles])
 * Call on any protected page.
 * Optionally pass roles that are allowed, e.g. requireAuth(["admin"])
 */
window.requireAuth = function (allowedRoles = []) {
  const user = window.authManager.getCurrentUser();
  if (!user) {
    showAuthMessage("Please log in to access this page.", "error");
    setTimeout(() => {
      window.location.href = "login.html";
    }, 1500);
    return false;
  }
  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    showAuthMessage("You don't have permission to view this page.", "error");
    setTimeout(() => {
      window.location.href = "unauthorized.html";
    }, 1500);
    return false;
  }
  return true;
};

/** Redirect already-logged-in users away from login/register pages */
window.redirectIfLoggedIn = function () {
  const user = window.authManager.getCurrentUser();
  if (user) {
    window.location.href = window.authManager.getHomePageForRole(user.role);
  }
};

// ─────────────────────────────────────────────
// showAuthMessage — kept exactly from old auth.js
// ─────────────────────────────────────────────
window.showAuthMessage = function (message, type = "info") {
  const existing = document.querySelector(".auth-message");
  if (existing) existing.remove();

  const div = document.createElement("div");
  div.className = `auth-message auth-message-${type}`;
  div.innerHTML = `
    <div class="auth-message-content">
      <i class="fas fa-${type === "success" ? "check-circle" : type === "error" ? "exclamation-circle" : "info-circle"}"></i>
      <span>${message}</span>
    </div>`;

  div.style.cssText = `
    position:fixed; top:20px; right:20px; z-index:10000;
    padding:15px 20px; border-radius:8px; color:white;
    font-weight:500; box-shadow:0 4px 12px rgba(0,0,0,.15);
    animation:slideInRight .3s ease-out; max-width:400px;`;

  const colors = {
    success: "linear-gradient(135deg,#4caf50,#45a049)",
    error: "linear-gradient(135deg,#f44336,#e53935)",
    info: "linear-gradient(135deg,#2196f3,#1976d2)",
  };
  div.style.background = colors[type] || colors.info;
  document.body.appendChild(div);

  setTimeout(() => {
    if (div.parentNode) {
      div.style.animation = "slideOutRight .3s ease-out";
      setTimeout(() => div.remove(), 300);
    }
  }, 5000);
};

// CSS animations (same as before)
const s = document.createElement("style");
s.textContent = `
  @keyframes slideInRight  { from{opacity:0;transform:translateX(100%)} to{opacity:1;transform:translateX(0)} }
  @keyframes slideOutRight { from{opacity:1;transform:translateX(0)}    to{opacity:0;transform:translateX(100%)} }
  .auth-message-content { display:flex; align-items:center; gap:10px; }
  .auth-message-content i { font-size:1.2rem; }
`;
document.head.appendChild(s);

// Run UI update on every page load
document.addEventListener("DOMContentLoaded", () => {
  window.authManager.updateAuthUI();
});
