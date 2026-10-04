let currentToken = localStorage.getItem("securecare_token") || null;

document.addEventListener("DOMContentLoaded", () => {
    if (currentToken) {
        testFetchMe();
    }
});

function switchTab(tab) {
    const regBtn = document.getElementById("tabRegisterBtn");
    const loginBtn = document.getElementById("tabLoginBtn");
    const regForm = document.getElementById("registerForm");
    const loginForm = document.getElementById("loginForm");
    clearAlert("authAlert");

    if (tab === "register") {
        regBtn.classList.add("active");
        loginBtn.classList.remove("active");
        regForm.style.display = "block";
        loginForm.style.display = "none";
    } else {
        loginBtn.classList.add("active");
        regBtn.classList.remove("active");
        loginForm.style.display = "block";
        regForm.style.display = "none";
    }
}

function showAlert(elemId, type, message) {
    const el = document.getElementById(elemId);
    el.className = `alert alert-${type}`;
    el.textContent = message;
    el.style.display = "block";
}

function clearAlert(elemId) {
    const el = document.getElementById(elemId);
    el.style.display = "none";
    el.textContent = "";
}

function appendConsole(action, details) {
    const consoleBox = document.getElementById("consoleLog");
    const timestamp = new Date().toLocaleTimeString();
    const formatted = `[${timestamp}] ${action}\n${typeof details === "string" ? details : JSON.stringify(details, null, 2)}\n\n`;
    
    if (consoleBox.textContent.startsWith("//")) {
        consoleBox.textContent = formatted;
    } else {
        consoleBox.textContent = formatted + consoleBox.textContent;
    }
}

function clearConsole() {
    document.getElementById("consoleLog").textContent = "// Console cleared.";
}

async function handleRegister(e) {
    e.preventDefault();
    clearAlert("authAlert");

    const username = document.getElementById("regUsername").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value;
    const fullName = document.getElementById("regFullName").value.trim();

    const payload = {
        username: username,
        email: email,
        password: password,
        full_name: fullName || null,
        role: "PATIENT"
    };

    appendConsole("POST /api/auth/register Request Payload:", {
        ...payload,
        password: "[PROTECTED - WILL BE HASHED BEFORE STORAGE]"
    });

    try {
        const res = await fetch("/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        appendConsole(`POST /api/auth/register Response (${res.status} ${res.statusText}):`, data);

        if (res.ok) {
            showAlert("authAlert", "success", `Registration successful for user '${data.username}'! You can now sign in.`);
            document.getElementById("registerForm").reset();
            switchTab("login");
            document.getElementById("loginIdentifier").value = username;
        } else {
            const errorMsg = data.detail || (Array.isArray(data.detail) ? data.detail.map(d => d.msg).join(", ") : "Registration failed.");
            showAlert("authAlert", "error", errorMsg);
        }
    } catch (err) {
        appendConsole("POST /api/auth/register Error:", err.message);
        showAlert("authAlert", "error", "Network or server connection error.");
    }
}

async function handleLogin(e) {
    e.preventDefault();
    clearAlert("authAlert");

    const identifier = document.getElementById("loginIdentifier").value.trim();
    const password = document.getElementById("loginPassword").value;

    const payload = {
        username: identifier,
        password: password
    };

    appendConsole("POST /api/auth/login Request:", {
        username: identifier,
        password: "[PROTECTED]"
    });

    try {
        const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        appendConsole(`POST /api/auth/login Response (${res.status} ${res.statusText}):`, {
            access_token: data.access_token ? `${data.access_token.substring(0, 16)}...` : undefined,
            token_type: data.token_type,
            role: data.role,
            error: data.detail
        });

        if (res.ok && data.access_token) {
            currentToken = data.access_token;
            localStorage.setItem("securecare_token", currentToken);
            showAlert("authAlert", "success", "Authentication successful! Fetching user profile...");
            await testFetchMe();
        } else {
            const errorMsg = data.detail || "Authentication failed.";
            showAlert("authAlert", "error", errorMsg);
        }
    } catch (err) {
        appendConsole("POST /api/auth/login Error:", err.message);
        showAlert("authAlert", "error", "Network or server error during sign in.");
    }
}

async function testFetchMe() {
    if (!currentToken) {
        showAlert("authAlert", "error", "No active JWT token found.");
        return;
    }

    appendConsole("GET /api/auth/me Request Headers:", {
        Authorization: `Bearer ${currentToken.substring(0, 16)}...`
    });

    try {
        const res = await fetch("/api/auth/me", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${currentToken}`
            }
        });

        const data = await res.json();
        appendConsole(`GET /api/auth/me Response (${res.status} ${res.statusText}):`, data);

        if (res.ok) {
            document.getElementById("authSection").style.display = "none";
            document.getElementById("profileSection").style.display = "block";

            document.getElementById("profId").textContent = data.id;
            document.getElementById("profUsername").textContent = data.username;
            document.getElementById("profEmail").textContent = data.email;
            document.getElementById("profRole").textContent = data.role;
            document.getElementById("profActive").textContent = data.is_active ? "Yes (Active)" : "No";
            document.getElementById("profCreated").textContent = new Date(data.created_at).toLocaleString();

            showAlert("profileAlert", "success", "Verified: Protected endpoint returned sanitized user profile (no hashed password).");
        } else {
            handleLogout();
            showAlert("authAlert", "error", "Session expired or invalid. Please sign in again.");
        }
    } catch (err) {
        appendConsole("GET /api/auth/me Error:", err.message);
    }
}

function handleLogout() {
    currentToken = null;
    localStorage.removeItem("securecare_token");
    document.getElementById("profileSection").style.display = "none";
    document.getElementById("authSection").style.display = "block";
    clearAlert("profileAlert");
    clearAlert("authAlert");
    appendConsole("Session Cleared", "Signed out and discarded local JWT token.");
}
