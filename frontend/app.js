/**
 * Census Assistant - Client Application Core
 * Router, Multilingual Translation Engine, API Integration, Real-Time Search, and Voice Assistant.
 */

// ==================== 1. MULTILINGUAL DICTIONARY ====================
const I18N = {
  en: {
    app_title: "Census Assistant",
    app_tagline: "Precision through Clarity",
    circle_name: "Lakhipur Circle",
    credits: "By Shahin Sha A. - S. A. Ahmed",
    sign_in: "Sign In",
    sign_in_sub: "Enter your credentials to access census records",
    nav_home: "Home",
    nav_search: "Search",
    nav_assistant: "Assistant",
    nav_manual: "Manuals",
    nav_supervisor: "Supervisor",
    nav_attendance: "Attendance",
    nav_alerts: "Alerts",
    nav_settings: "Settings",
    nav_admin: "Admin",
    attendance_title: "Mark Today's Attendance",
    attendance_home_sub: "Submit your name, position, block number, photo and live location.",
    search_placeholder: "Ask anything about Census or search HLB...",
    chat_wa: "Chat on WhatsApp",
    ask_ai: "Ask AI",
    search_records: "Search Records",
    search_sub: "Filter and review assigned census functionaries and HLB blocks.",
    manuals: "Manuals",
    manuals_guidelines: "Manuals & Guidelines",
    supervisor_info: "Supervisor Info",
    recent_activity: "Recent Activity",
    view_all: "View All",
    official_updates: "Official Updates",
    app_settings: "App Settings",
    language: "Language",
    dark_theme: "Dark Theme",
    push_notifications: "Push Notifications",
    contact_tech_assistant: "Contact Technical Assistant",
    sign_out: "Sign Out Securely"
  },
  as: {
    app_title: "লোকপিয়ল সহায়ক (Census Assistant)",
    app_tagline: "স্পষ্টতাৰ জৰিয়তে নিখুঁততা",
    circle_name: "লাক্ষীপুৰ চাৰ্কেল",
    credits: "শ্বাহীন শ্বাহ এ. - এছ. এ. আহমেদ দ্বাৰা",
    sign_in: "লগ ইন কৰক",
    sign_in_sub: "লোকপিয়ল তথ্য চাবলৈ মোবাইল নম্বৰ প্ৰৱেশ কৰক",
    nav_home: "গৃহ (Home)",
    nav_search: "সন্ধান (Search)",
    nav_assistant: "এআই সহায়ক",
    nav_manual: "মেনুৱেল",
    nav_supervisor: "পৰ্যবেক্ষক",
    nav_attendance: "উপস্থিতি",
    nav_alerts: "বিজ্ঞপ্তি",
    nav_settings: "ছেটিংছ",
    nav_admin: "এডমিন",
    attendance_title: "আজিৰ উপস্থিতি দিয়ক",
    attendance_home_sub: "নাম, পদ, ব্লক নম্বৰ, ফটো আৰু বৰ্তমানৰ অৱস্থান দাখিল কৰক।",
    search_placeholder: "লোকপিয়ল বা HLB সম্পৰ্কে যিকোনো প্ৰশ্ন সুধক...",
    chat_wa: "হোৱাটছএপত বাৰ্তালাপ কৰক",
    ask_ai: "এআই ক সোধক",
    search_records: "নথি সন্ধান কৰক",
    search_sub: "লোকপিয়ল কৰ্মী আৰু আবণ্টিত HLB ব্লকৰ তালিকা চাওক।",
    manuals: "নিৰ্দেশাৱলী",
    manuals_guidelines: "নিৰ্দেশনা আৰু মেনুৱেল",
    supervisor_info: "পৰ্যবেক্ষকৰ তথ্য",
    recent_activity: "শেহতীয়া কাৰ্যকলাপ",
    view_all: "সকলো চাওক",
    official_updates: "চৰকাৰী আপডেট",
    app_settings: "এপ্লিকেচন ছেটিংছ",
    language: "ভাষা (Language)",
    dark_theme: "ডাৰ্ক মোড",
    push_notifications: "জাননী (Notifications)",
    contact_tech_assistant: "কাৰিকৰী সহায়কৰ সৈতে যোগাযোগ",
    sign_out: "লগ আউট কৰক"
  },
  hi: {
    app_title: "जनगणना सहायक (Census Assistant)",
    app_tagline: "स्पष्टता के माध्यम से सटीकता",
    circle_name: "लखीपुर सर्कल",
    credits: "द्वारा शाहीन शाह ए. - एस. ए. अहमद",
    sign_in: "साइन इन करें",
    sign_in_sub: "जनगणना रिकॉर्ड देखने के लिए मोबाइल दर्ज करें",
    nav_home: "होम (Home)",
    nav_search: "खोजें (Search)",
    nav_assistant: "एआई सहायक",
    nav_manual: "नियमावली",
    nav_supervisor: "पर्यवेक्षक",
    nav_attendance: "उपस्थिति",
    nav_alerts: "सूचनाएं",
    nav_settings: "सेटिंग्स",
    nav_admin: "व्यवस्थापक",
    attendance_title: "आज की उपस्थिति दर्ज करें",
    attendance_home_sub: "नाम, पद, ब्लॉक संख्या, फोटो और वर्तमान स्थान जमा करें।",
    search_placeholder: "जनगणना या HLB ब्लॉक के बारे में पूछें...",
    chat_wa: "व्हाट्सएप पर चैट करें",
    ask_ai: "एआई से पूछें",
    search_records: "रिकॉर्ड खोजें",
    search_sub: "आवंटित जनगणना कर्मियों और HLB ब्लॉकों की सूची देखें।",
    manuals: "नियमावली",
    manuals_guidelines: "दिशानिर्देश एवं नियमावली",
    supervisor_info: "पर्यवेक्षक विवरण",
    recent_activity: "हाल की गतिविधि",
    view_all: "सभी देखें",
    official_updates: "आधिकारिक अपडेट",
    app_settings: "ऐप सेटिंग्स",
    language: "भाषा (Language)",
    dark_theme: "डार्क थीम",
    push_notifications: "पुश सूचनाएं",
    contact_tech_assistant: "तकनीकी सहायक से संपर्क करें",
    sign_out: "सुरक्षित साइन आउट"
  },
  bn: {
    app_title: "আদমশুমারি সহকারী (Census Assistant)",
    app_tagline: "স্পষ্টতার মাধ্যমে নির্ভুলতা",
    circle_name: "লাখিপুর সার্কেল",
    credits: "শাহীন শাহ এ. - এস. এ. আহমেদ দ্বারা",
    sign_in: "সাইন ইন করুন",
    sign_in_sub: "আদমশুমারি রেকর্ড দেখতে মোবাইল নম্বর লিখুন",
    nav_home: "হোম (Home)",
    nav_search: "অনুসন্ধান",
    nav_assistant: "এআই সহকারী",
    nav_manual: "ম্যানুয়াল",
    nav_supervisor: "তত্ত্বাবধায়ক",
    nav_attendance: "উপস্থিতি",
    nav_alerts: "বিজ্ঞপ্তি",
    nav_settings: "সেটিংস",
    nav_admin: "অ্যাডমিন",
    attendance_title: "আজকের উপস্থিতি দিন",
    attendance_home_sub: "নাম, পদ, ব্লক নম্বর, ছবি এবং বর্তমান অবস্থান জমা দিন।",
    search_placeholder: "আদমশুমারি বা HLB ব্লক সম্পর্কে প্রশ্ন করুন...",
    chat_wa: "হোয়াটসঅ্যাপে চ্যাট করুন",
    ask_ai: "এআই কে জিজ্ঞাসা করুন",
    search_records: "রেকর্ড খুঁজুন",
    search_sub: "নির্ধারিত আদমশুমারি কর্মী ও HLB ব্লকের তালিকা দেখুন।",
    manuals: "ম্যানুয়াল",
    manuals_guidelines: "নির্দেশিকা ও ম্যানুয়াল",
    supervisor_info: "তত্ত্বাবধায়কের বিবরণ",
    recent_activity: "সাম্প্রতিক কার্যকলাপ",
    view_all: "সব দেখুন",
    official_updates: "অফিসিয়াল আপডেট",
    app_settings: "অ্যাপ সেটিংস",
    language: "ভাষা (Language)",
    dark_theme: "ডার্ক থিম",
    push_notifications: "পুশ বিজ্ঞপ্তি",
    contact_tech_assistant: "কারিগরি সহকারীর সাথে যোগাযোগ",
    sign_out: "সাইন আউট করুন"
  }
};

// ==================== 2. APPLICATION STATE ====================
const state = {
  currentLanguage: localStorage.getItem("census_lang") || "en",
  currentUser: JSON.parse(localStorage.getItem("census_user") || "null"),
  authToken: localStorage.getItem("census_token") || null,
  activeView: "home",
  recordsFilter: "all",
  recordsPage: 1,
  pendingMobileForOtp: "",
  searchDebounceTimer: null,

  // ----- Field attendance (see section 11) -----
  attendance: {
    record: null,           // today's saved record for the entered mobile, if any
    photoBlob: null,        // downsized JPEG waiting to be uploaded
    photoName: "",
    location: null,         // { latitude, longitude, accuracy }
    lookupTimer: null,
    editing: false
  },
  adminAttendance: {
    status: "",
    searchTimer: null,
    photoObjectUrl: null,
    rejectTargetId: null
  }
};

// ==================== ANDROID BRIDGE HELPERS ====================
// Detect if running inside Android WebView with native bridge
const isAndroid = typeof window.AndroidBridge !== "undefined";

/**
 * Returns the correct API base URL.
 * - When loaded from Flask directly: empty string (relative paths work).
 * - When loaded from file:// (offline bundle): use injected BACKEND_URL.
 */
function getApiBase() {
  if (window.location.protocol === "file:") {
    return window.BACKEND_URL || "http://10.0.2.2:8080";
  }
  return "";
}

/**
 * Fetch wrapper that prepends the API base URL so file:// loads
 * can still reach the Flask backend over the network.
 */
async function apiFetch(path, options = {}) {
  const url = getApiBase() + path;
  if (state.authToken) {
    // Auto-attach the bearer token so admin-gated endpoints (and any
    // per-user endpoints) authenticate without every call site having
    // to remember to set the header itself.
    const headers = new Headers(options.headers || {});
    if (!headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${state.authToken}`);
    }
    options = { ...options, headers };
  }
  return fetch(url, options);
}

/**
 * Open phone dialer — uses native Android intent when available,
 * falls back to tel: link in browser.
 */
function nativeCall(phoneNumber) {
  const clean = phoneNumber.replace(/[^\d+]/g, "");
  if (isAndroid) {
    window.AndroidBridge.callPhone(clean);
  } else {
    window.open("tel:" + clean, "_self");
  }
}

/**
 * Open WhatsApp with a pre-filled message — uses native Android
 * intent when available, falls back to wa.me URL.
 */
function nativeWhatsApp(phoneNumber, message = "") {
  const clean = phoneNumber.replace(/[^\d+]/g, "");
  if (isAndroid) {
    window.AndroidBridge.openWhatsApp(clean, message);
  } else {
    const encoded = encodeURIComponent(message);
    window.open(`https://wa.me/${clean}?text=${encoded}`, "_blank");
  }
}

/**
 * Share text — uses native Android share sheet or Web Share API,
 * falling back to clipboard copy.
 */
function nativeShare(title, text) {
  if (isAndroid) {
    window.AndroidBridge.shareText(title, text);
  } else if (navigator.share) {
    navigator.share({ title, text }).catch(() => {});
  } else {
    navigator.clipboard.writeText(text);
    showToast("Response copied to share!");
  }
}

// ==================== 3. INITIALIZATION & ROUTING ====================
document.addEventListener("DOMContentLoaded", async () => {
  // Check theme
  if (localStorage.getItem("census_dark") === "true") {
    document.documentElement.classList.add("dark");
    const toggle = document.getElementById("toggle-dark-mode");
    if (toggle) toggle.checked = true;
  }

  // Set language
  applyLanguage(state.currentLanguage);
  const langSelect = document.getElementById("header-lang-select");
  if (langSelect) langSelect.value = state.currentLanguage;

  // Splash Screen Timeout
  setTimeout(() => {
    const splash = document.getElementById("view-splash");
    if (splash) splash.classList.add("hidden");

    if (state.authToken && state.currentUser) {
      showAppShell();
      updateUserHeader();
      applyRoleBasedNav();
      handleRouteFromHash();
      refreshHomeAttendanceStatus();
    } else {
      showLoginView();
    }
  }, 1200);

  // Load initial data
  loadNotifications();
});

window.addEventListener("hashchange", handleRouteFromHash);

function handleRouteFromHash() {
  const hash = window.location.hash.replace("#", "") || "home";
  navigateTo(hash, false);
}

function showLoginView() {
  document.getElementById("app-shell").classList.add("hidden");
  document.getElementById("view-login").classList.remove("hidden");
}

function showAppShell() {
  document.getElementById("view-login").classList.add("hidden");
  document.getElementById("app-shell").classList.remove("hidden");
}

function navigateTo(viewName, updateHash = true) {
  const validViews = ["home", "search", "chat", "manual", "supervisor", "attendance", "notifications", "settings", "admin"];
  if (!validViews.includes(viewName)) viewName = "home";

  // Major Issue guard: the admin portal is only for the Technical Assistant
  // admin account (role === "admin"). Guests and OTP-authenticated field
  // functionaries are redirected away even if they try to reach #admin
  // directly via the URL hash.
  if (viewName === "admin" && (!state.currentUser || state.currentUser.role !== "admin")) {
    showToast("Admin portal is restricted to Technical Assistants.");
    viewName = "home";
    updateHash = true;
  }

  state.activeView = viewName;
  if (updateHash) {
    window.location.hash = viewName;
  }

  // Hide all view sections
  validViews.forEach(v => {
    const el = document.getElementById(`page-${v}`);
    if (el) el.classList.add("hidden");

    // Desktop nav styling
    const dNav = document.getElementById(`nav-desktop-${v}`);
    if (dNav) {
      if (v === viewName) {
        dNav.classList.add("bg-primary-container", "text-on-primary-container", "font-bold");
        dNav.classList.remove("text-on-surface-variant");
      } else {
        dNav.classList.remove("bg-primary-container", "text-on-primary-container", "font-bold");
        dNav.classList.add("text-on-surface-variant");
      }
    }

    // Mobile nav styling
    const mNav = document.getElementById(`nav-mobile-${v}`);
    if (mNav) {
      if (v === viewName) {
        mNav.classList.add("bg-primary-container", "text-on-primary-container", "rounded-full");
        mNav.classList.remove("text-on-surface-variant");
      } else {
        mNav.classList.remove("bg-primary-container", "text-on-primary-container", "rounded-full");
        mNav.classList.add("text-on-surface-variant");
      }
    }
  });

  // Show active view section
  const target = document.getElementById(`page-${viewName}`);
  if (target) target.classList.remove("hidden");

  // Update header title
  const titles = {
    home: "Census Assistant",
    search: "Search Records",
    chat: "AI Chat Assistant",
    manual: "Manuals & Guidelines",
    supervisor: "Supervisor Details",
    attendance: "Field Attendance",
    notifications: "Official Updates",
    settings: "App Settings",
    admin: "Admin Control Center"
  };
  document.getElementById("page-header-title").textContent = titles[viewName] || "Census Assistant";

  // Specific view loaders
  if (viewName === "search") {
    state.recordsPage = 1;
    fetchRecords();
  } else if (viewName === "admin") {
    loadAdminStats();
    loadAdminNotices();
    loadUploadedFiles();
    loadAdminUsers();
    loadAdminQueryLogs();
    loadAdminAttendance();
    loadAiStatus();
    loadAdminAccounts();
    loadAuthAudit();
  } else if (viewName === "attendance") {
    initAttendanceView();
  } else if (viewName === "notifications") {
    loadNotifications();
  } else if (viewName === "supervisor") {
    loadSupervisors();
  } else if (viewName === "manual") {
    loadManualPage();
  }
}

/**
 * Major Issue guard (UI side): show/hide the Admin Panel nav entries based
 * on the signed-in user's role. Only role === "admin" (the seeded
 * Technical Assistant account, shahinxsha) ever sees these links — guest
 * and field-functionary sessions never get an admin link to click, on top
 * of the hash-based redirect in navigateTo() and the backend's
 * _require_admin() gate on every admin API route.
 */
function applyRoleBasedNav() {
  const isAdmin = !!(state.currentUser && state.currentUser.role === "admin");

  const desktopAdminLink = document.getElementById("nav-desktop-admin");
  if (desktopAdminLink) desktopAdminLink.classList.toggle("hidden", !isAdmin);

  const mobileAdminLink = document.getElementById("nav-mobile-drawer-admin");
  if (mobileAdminLink) mobileAdminLink.classList.toggle("hidden", !isAdmin);
}

// ==================== 4. AUTHENTICATION HANDLERS ====================
/**
 * Login tab switcher. "register" is a sub-view of the password tab rather
 * than a tab of its own, so the three-tab header stays as designed.
 */
function switchLoginTab(tab) {
  const forms = {
    otp: "form-otp",
    password: "form-password",
    register: "form-register",
    admin: "form-admin"
  };
  Object.values(forms).forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.add("hidden");
  });
  const active = document.getElementById(forms[tab] || forms.otp);
  if (active) active.classList.remove("hidden");

  // "register" keeps the Password tab highlighted.
  const highlighted = tab === "register" ? "password" : (forms[tab] ? tab : "otp");
  ["otp", "password", "admin"].forEach(name => {
    const btn = document.getElementById(`tab-btn-${name}`);
    if (!btn) return;
    if (name === highlighted) {
      btn.classList.add("border-primary", "text-primary");
      btn.classList.remove("border-transparent", "text-on-surface-variant");
    } else {
      btn.classList.remove("border-primary", "text-primary");
      btn.classList.add("border-transparent", "text-on-surface-variant");
    }
  });
}

function showRegisterForm() {
  switchLoginTab("register");
}

/**
 * Shared post-sign-in handling for every credential path (OTP, password,
 * admin). Stores the session, then either forces a password change or lands
 * the user in the app.
 */
function completeSignIn(data, landingView = "home", greeting = "") {
  state.authToken = data.token;
  state.currentUser = data.user;
  localStorage.setItem("census_token", data.token);
  localStorage.setItem("census_user", JSON.stringify(data.user));

  showAppShell();
  updateUserHeader();
  applyRoleBasedNav();

  if (data.must_change_password) {
    // The session is running on an admin-issued temporary password and the
    // backend refuses admin work until it is replaced, so ask immediately.
    openChangePasswordModal({ forced: true });
    return;
  }

  navigateTo(landingView);
  refreshHomeAttendanceStatus();
  if (greeting) showToast(greeting);
}

async function handleUserLogin(e) {
  e.preventDefault();
  const identifier = document.getElementById("user-identifier").value.trim();
  const password = document.getElementById("user-password").value;

  try {
    const res = await apiFetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier, password })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById("user-password").value = "";
      completeSignIn(data, "home", `Welcome back, ${data.user.name}.`);
    } else {
      showToast(data.message || "Sign-in failed.");
    }
  } catch (err) {
    showToast("Sign-in request failed. Check your connection.");
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const name = document.getElementById("reg-name").value.trim();
  const mobile = document.getElementById("reg-mobile").value.replace(/\D/g, "");
  const password = document.getElementById("reg-password").value;

  if (mobile.length !== 10) return showToast("Enter a valid 10-digit mobile number.");

  try {
    const res = await apiFetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, mobile_number: mobile, password })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById("reg-password").value = "";
      completeSignIn(data, "home", "Account created. Welcome!");
    } else {
      showToast(data.message || "Could not create the account.");
    }
  } catch (err) {
    showToast("Registration request failed.");
  }
}

async function handleForgotPassword() {
  const identifier = (document.getElementById("user-identifier").value || "").trim();
  if (!identifier) {
    return showToast("Enter your mobile number first, then tap Forgot password.");
  }
  try {
    const res = await apiFetch("/api/auth/forgot-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier })
    });
    const data = await res.json();
    showToast(data.message || "Request submitted.");
  } catch (err) {
    showToast("Could not submit the request.");
  }
}

// ---- Password change (forced after a temporary password, or voluntary) ----

function openChangePasswordModal(options = {}) {
  const { forced = false } = options;
  const modal = document.getElementById("modal-change-password");
  if (!modal) return;

  document.getElementById("change-password-title").textContent =
    forced ? "Set a new password" : "Change your password";
  document.getElementById("change-password-sub").textContent = forced
    ? "You signed in with a temporary password. Choose your own to continue."
    : "Enter your current password, then choose a new one.";

  // A forced change has no way out: the backend blocks admin work until the
  // temporary password is replaced, so offering Cancel would just dead-end.
  const cancel = document.getElementById("cp-cancel");
  if (cancel) cancel.classList.toggle("hidden", forced);

  ["cp-current", "cp-new", "cp-confirm"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  modal.dataset.forced = forced ? "1" : "";
  modal.classList.remove("hidden");
}

function closeChangePasswordModal() {
  const modal = document.getElementById("modal-change-password");
  if (modal && modal.dataset.forced !== "1") modal.classList.add("hidden");
}

async function handleChangePassword(e) {
  e.preventDefault();
  const current = document.getElementById("cp-current").value;
  const next = document.getElementById("cp-new").value;
  const confirm = document.getElementById("cp-confirm").value;

  if (next !== confirm) return showToast("The two new passwords do not match.");
  if (next.length < 8) return showToast("Password must be at least 8 characters long.");

  try {
    const res = await apiFetch("/api/auth/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_password: current, new_password: next })
    });
    const data = await res.json();
    if (!data.success) return showToast(data.message || "Could not update the password.");

    if (data.token) {
      state.authToken = data.token;
      localStorage.setItem("census_token", data.token);
    }
    if (state.currentUser) {
      state.currentUser.must_change_password = false;
      localStorage.setItem("census_user", JSON.stringify(state.currentUser));
    }
    const modal = document.getElementById("modal-change-password");
    modal.dataset.forced = "";
    modal.classList.add("hidden");

    showToast("Password updated.");
    navigateTo(state.currentUser && state.currentUser.role === "admin" ? "admin" : "home");
  } catch (err) {
    showToast("Could not update the password.");
  }
}

async function handleRequestOtp(e) {
  e.preventDefault();
  const mobileInput = document.getElementById("login-mobile");
  const mobile = mobileInput.value.trim();
  if (!mobile || mobile.length < 10) {
    showToast("Please enter a valid 10-digit mobile number.");
    return;
  }

  state.pendingMobileForOtp = mobile;
  try {
    const res = await apiFetch("/api/auth/request-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mobile_number: mobile })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById("otp-phone-display").textContent = `Code sent to +91 ${mobile}`;
      document.getElementById("modal-otp").classList.remove("hidden");
      if (data.debug_otp) {
        // Only ever present when the backend has DEV_OTP_BYPASS enabled for local testing.
        document.getElementById("otp-input").value = data.debug_otp;
        showToast(`Verification code sent! (Dev code: ${data.debug_otp})`);
      } else {
        showToast("Verification code sent to your mobile number.");
      }
    } else {
      showToast(data.message || "Failed to send OTP.");
    }
  } catch (err) {
    showToast("Network error requesting OTP.");
  }
}

async function handleVerifyOtp(e) {
  e.preventDefault();
  const otp = document.getElementById("otp-input").value.trim();
  try {
    const res = await apiFetch("/api/auth/verify-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mobile_number: state.pendingMobileForOtp, otp: otp })
    });
    const data = await res.json();
    if (data.success) {
      state.authToken = data.token;
      state.currentUser = data.user;
      localStorage.setItem("census_token", data.token);
      localStorage.setItem("census_user", JSON.stringify(data.user));
      closeOtpModal();
      showAppShell();
      updateUserHeader();
      applyRoleBasedNav();
      navigateTo("home");
      showToast(`Welcome ${data.user.name}!`);
    } else {
      showToast(data.message || "Invalid OTP code.");
    }
  } catch (err) {
    showToast("Error verifying code.");
  }
}

async function handleAdminLogin(e) {
  e.preventDefault();
  const username = document.getElementById("admin-user").value.trim();
  const password = document.getElementById("admin-pass").value.trim();

  try {
    const res = await apiFetch("/api/auth/admin-login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById("admin-pass").value = "";
      completeSignIn(data, "admin", "Signed in as Administrator.");
    } else {
      showToast(data.message || "Invalid admin credentials.");
    }
  } catch (err) {
    showToast("Login request failed.");
  }
}

async function handleGuestLogin() {
  try {
    const res = await apiFetch("/api/auth/guest", { method: "POST" });
    const data = await res.json();
    state.authToken = data.token;
    state.currentUser = data.user;
    localStorage.setItem("census_token", data.token);
    localStorage.setItem("census_user", JSON.stringify(data.user));
    showAppShell();
    updateUserHeader();
    applyRoleBasedNav();
    navigateTo("home");
    showToast("Signed in as Guest.");
  } catch (err) {
    showToast("Could not initiate guest session.");
  }
}

function handleSignOut() {
  state.authToken = null;
  state.currentUser = null;
  localStorage.removeItem("census_token");
  localStorage.removeItem("census_user");
  showLoginView();
  showToast("Signed out successfully.");
}

function updateUserHeader() {
  if (!state.currentUser) return;
  const nameEl = document.getElementById("user-display-name");
  const roleEl = document.getElementById("user-display-role");
  const initialsEl = document.getElementById("user-avatar-initials");

  if (nameEl) nameEl.textContent = state.currentUser.name || "Guest User";
  if (roleEl) roleEl.textContent = state.currentUser.functionary_type || state.currentUser.role || "Guest";
  
  if (initialsEl && state.currentUser.name) {
    const parts = state.currentUser.name.split(" ");
    const initials = parts.length > 1 ? (parts[0][0] + parts[1][0]) : parts[0].slice(0, 2);
    initialsEl.textContent = initials.toUpperCase();
  }
}

function closeOtpModal() {
  document.getElementById("modal-otp").classList.add("hidden");
}

function resendOtp() {
  if (state.pendingMobileForOtp) {
    handleRequestOtp({ preventDefault: () => {} });
  }
}

// ==================== 5. AI CHAT ASSISTANT HANDLERS ====================
async function handleSendChat(e) {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const query = input.value.trim();
  if (!query) return;

  input.value = "";
  appendChatMessage("user", query);

  // Append thinking skeleton
  const thinkingId = appendChatSkeleton();

  try {
    const res = await apiFetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        lang: state.currentLanguage,
        model: "gemini-2.5-flash"
      })
    });
    const data = await res.json();
    removeChatSkeleton(thinkingId);
    appendChatMessage("ai", data.answer, data.citations, data.intent,
                      data.web_searched, data.searches_remaining_today, data.answered_by);
  } catch (err) {
    removeChatSkeleton(thinkingId);
    appendChatMessage("ai", "I encountered a connection error. Please check your network or try again.", []);
  }
}

function quickAsk(text) {
  closePdfModal();
  navigateTo("chat");
  const input = document.getElementById("chat-input");
  if (input) {
    input.value = text;
    handleSendChat({ preventDefault: () => {} });
  }
}

function executeHomeSearch() {
  const query = document.getElementById("home-search-input").value.trim();
  if (query) {
    quickAsk(query);
  }
}

function appendChatMessage(sender, text, citations = [], intent = "", webSearched = false,
                           searchesRemaining = null, answeredBy = "") {
  const container = document.getElementById("chat-messages");
  if (!container) return;

  const msgDiv = document.createElement("div");
  msgDiv.className = "animate-fade-in flex flex-col gap-1.5 w-full";

  if (sender === "user") {
    msgDiv.className += " items-end";
    msgDiv.innerHTML = `
      <div class="bg-primary-container text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[85%] md:max-w-[70%] shadow-sm text-sm leading-relaxed">
        ${escapeHtml(text)}
      </div>
    `;
  } else {
    msgDiv.className += " items-start";
    
    let footerHtml = "";
    // Offline mode is stated plainly rather than left to look like a normal
    // answer — a user is entitled to know the assistant could not consult the
    // AI service for this one.
    if (answeredBy === "offline_fallback") {
      footerHtml += `
        <div class="flex items-center gap-1.5 text-[11px] text-[#8a6100] mt-2 font-medium">
          <span class="material-symbols-outlined text-[14px]">cloud_off</span>
          <span>Offline mode — answered from local records only</span>
        </div>`;
    }
    if (webSearched) {
      const quotaText = searchesRemaining != null ? ` • ${searchesRemaining}/10 searches left today` : "";
      footerHtml += `
        <div class="flex items-center gap-1.5 text-[11px] text-tertiary-container mt-2 font-medium">
          <span class="material-symbols-outlined text-[14px]">public</span>
          <span>Web Search Grounded${escapeHtml(quotaText)}</span>
        </div>`;
    }
    if (citations && citations.length > 0) {
      footerHtml += `
        <div class="flex items-center gap-1 text-[11px] text-outline mt-1.5">
          <span class="material-symbols-outlined text-[13px]">database</span>
          <span>Source: ${escapeHtml(citations.join(" | "))}</span>
        </div>`;
    }

    msgDiv.innerHTML = `
      <div class="flex items-start gap-3 max-w-[95%] md:max-w-[80%]">
        <div class="w-8 h-8 rounded-full bg-primary-container text-white flex items-center justify-center shrink-0 mt-1">
          <span class="material-symbols-outlined text-lg">smart_toy</span>
        </div>
        <div class="flex flex-col gap-1 flex-1">
          <div class="bg-surface-container-lowest text-on-surface rounded-2xl rounded-tl-sm p-4 shadow-sm border border-outline-variant/30 text-sm leading-relaxed">
            ${formatMarkdown(text)}
            ${footerHtml}
          </div>
          <!-- Action Buttons -->
          <div class="flex items-center gap-2 px-2 text-on-surface-variant">
            <button onclick="copyToClipboard(this)" class="p-1 hover:bg-surface-container rounded-full text-xs" title="Copy Response">
              <span class="material-symbols-outlined text-base">content_copy</span>
            </button>
            <button onclick="shareText('${escapeAttr(text)}')" class="p-1 hover:bg-surface-container rounded-full text-xs" title="Share">
              <span class="material-symbols-outlined text-base">share</span>
            </button>
            <button onclick="showToast('Thank you for your feedback!')" class="p-1 hover:bg-surface-container rounded-full text-xs" title="Good Response">
              <span class="material-symbols-outlined text-base">thumb_up</span>
            </button>
            <button onclick="showToast('Feedback noted for improvement.')" class="p-1 hover:bg-surface-container rounded-full text-xs" title="Bad Response">
              <span class="material-symbols-outlined text-base">thumb_down</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function appendChatSkeleton() {
  const container = document.getElementById("chat-messages");
  const id = `skeleton-${Date.now()}`;
  const skel = document.createElement("div");
  skel.id = id;
  skel.className = "flex items-start gap-3 max-w-[80%] animate-fade-in";
  skel.innerHTML = `
    <div class="w-8 h-8 rounded-full bg-primary-container text-white flex items-center justify-center shrink-0 mt-1">
      <span class="material-symbols-outlined text-lg">smart_toy</span>
    </div>
    <div class="bg-surface-container-lowest border border-outline-variant/30 rounded-2xl p-4 shadow-sm flex items-center gap-2">
      <span class="w-2 h-2 rounded-full bg-primary animate-bounce"></span>
      <span class="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:0.2s]"></span>
      <span class="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:0.4s]"></span>
    </div>
  `;
  container.appendChild(skel);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeChatSkeleton(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ==================== 6. RECORDS SEARCH HANDLERS ====================
function debounceRecordsSearch() {
  clearTimeout(state.searchDebounceTimer);
  state.searchDebounceTimer = setTimeout(() => {
    state.recordsPage = 1;
    fetchRecords();
  }, 300);
}

function setSearchFilter(filterName) {
  state.recordsFilter = filterName;
  state.recordsPage = 1;

  ["all", "name", "mobile", "id", "hlb", "supervisor"].forEach(f => {
    const btn = document.getElementById(`filter-${f}`);
    if (btn) {
      if (f === filterName) {
        btn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold border border-primary bg-primary text-white transition-colors";
      } else {
        btn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold border border-outline-variant bg-surface-container-lowest text-on-surface-variant hover:bg-surface-variant/40 transition-colors";
      }
    }
  });

  fetchRecords();
}

async function fetchRecords(append = false) {
  const query = document.getElementById("records-search-input").value.trim();
  const listContainer = document.getElementById("records-results-list");
  
  if (!append) {
    listContainer.innerHTML = `
      <div class="flex justify-center p-8">
        <div class="loader-spinner-primary"></div>
      </div>
    `;
    state.recordsCache = {};
  }

  try {
    const res = await apiFetch(`/api/records/search?q=${encodeURIComponent(query)}&filter=${state.recordsFilter}&page=${state.recordsPage}&limit=12`);
    const data = await res.json();

    if (!append) {
      listContainer.innerHTML = "";
    }

    if (!data.results || data.results.length === 0) {
      if (!append) {
        listContainer.innerHTML = `
          <div class="bg-surface-container-lowest border border-outline-variant/30 rounded-2xl p-8 text-center text-on-surface-variant">
            <span class="material-symbols-outlined text-4xl text-outline mb-2">search_off</span>
            <p class="text-sm font-semibold">No records found matching your query.</p>
            <p class="text-xs text-outline mt-1">Try changing filter tags or searching by HLB block number.</p>
          </div>
        `;
      }
      document.getElementById("btn-load-more-records").classList.add("hidden");
      return;
    }

    state.recordsCache = state.recordsCache || {};

    data.results.forEach(rec => {
      state.recordsCache[rec.user_id] = rec;
      const card = document.createElement("article");
      card.className = "bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:bg-surface-container-low transition-all cursor-pointer group";
      card.onclick = () => openRecordProfile(rec.user_id);
      
      const cleanMob = (rec.mobile || "8453441975").replace(/[^0-9]/g, "");
      const waMsg = `Inquiry regarding ${rec.name}${rec.hlb_number ? ` (HLB ${rec.hlb_number})` : ""}`;
      const mapsBtnHtml = rec.maps_url
        ? `<a href="${escapeAttr(rec.maps_url)}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation();"
             class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 text-primary hover:bg-primary hover:text-white transition-colors text-xs font-semibold shrink-0">
             <span class="material-symbols-outlined text-[16px]">map</span>
             <span>${escapeHtml(rec.area_name || "View Map")}</span>
           </a>`
        : "";

      // HLB/Supervisor/Circle only apply to individual block-level roles
      // (Enumerators). Supervisors and other roles never have their own
      // HLB by design, so showing "—" placeholders for them read like
      // missing data — just omit that row instead. An Enumerator with no
      // HLB match, on the other hand, IS a real gap (registered but not
      // yet assigned a block) — flag it clearly rather than blanking it.
      const isEnumeratorRole = /enumerator/i.test(rec.role || "");
      const allocationRowHtml = isEnumeratorRole
        ? (rec.hlb_number
            ? `<span class="flex items-center gap-1"><span class="material-symbols-outlined text-[15px] text-primary">tag</span> HLB: <strong>${escapeHtml(rec.hlb_number)}</strong></span>
               <span class="flex items-center gap-1"><span class="material-symbols-outlined text-[15px]">supervisor_account</span> Supervisor: ${escapeHtml(rec.supervisor || "—")}</span>
               <span class="flex items-center gap-1"><span class="material-symbols-outlined text-[15px]">pin_drop</span> Circle: ${escapeHtml(rec.circle || "—")}</span>`
            : `<span class="flex items-center gap-1 text-amber-600 font-semibold"><span class="material-symbols-outlined text-[15px]">error_outline</span> HLB block not yet allocated</span>`)
        : "";

      card.innerHTML = `
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <h3 class="text-base font-bold text-on-surface group-hover:text-primary transition-colors truncate">${escapeHtml(rec.name)}</h3>
            <span class="text-[10px] px-2 py-0.5 rounded bg-primary-fixed text-primary font-semibold">${escapeHtml(rec.role)}</span>
          </div>
          <div class="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-on-surface-variant mt-2">
            <span class="flex items-center gap-1"><span class="material-symbols-outlined text-[15px]">badge</span> ID: <code class="font-mono font-bold">${escapeHtml(rec.user_id)}</code></span>
            ${allocationRowHtml}
            ${rec.area_name ? `<span class="flex items-center gap-1 text-primary"><span class="material-symbols-outlined text-[15px]">location_on</span> ${escapeHtml(rec.area_name)}</span>` : ""}
          </div>
        </div>
        <div class="flex items-center gap-2 w-full md:w-auto justify-end pt-3 md:pt-0 border-t border-outline-variant/20 md:border-t-0 shrink-0">
          ${mapsBtnHtml}
          <button onclick="event.stopPropagation(); nativeCall('${escapeAttr(cleanMob)}')" class="w-9 h-9 rounded-full bg-surface-container border border-outline-variant/30 flex items-center justify-center text-primary hover:bg-primary hover:text-white transition-colors" title="Call +91 ${escapeHtml(rec.mobile || '8453441975')}">
            <span class="material-symbols-outlined text-[17px]" style="font-variation-settings:'FILL' 1">call</span>
          </button>
          <button onclick="event.stopPropagation(); nativeWhatsApp('91${escapeAttr(cleanMob)}', '${escapeAttr(waMsg)}')" class="w-9 h-9 rounded-full bg-surface-container border border-outline-variant/30 flex items-center justify-center text-[#25D366] hover:bg-[#25D366] hover:text-white transition-colors" title="Message on WhatsApp">
            <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"></path></svg>
          </button>
          <button onclick="quickAsk('Show details for ${escapeAttr(rec.name)}')" class="w-9 h-9 rounded-full bg-surface-container border border-outline-variant/30 flex items-center justify-center text-primary hover:bg-primary hover:text-white transition-colors" title="Query AI for Details">
            <span class="material-symbols-outlined text-lg">chevron_right</span>
          </button>
        </div>
      `;
      listContainer.appendChild(card);
    });

    const loadMoreBtn = document.getElementById("btn-load-more-records");
    if (data.results.length >= 12) {
      loadMoreBtn.classList.remove("hidden");
    } else {
      loadMoreBtn.classList.add("hidden");
    }

  } catch (err) {
    listContainer.innerHTML = `<p class="text-xs text-error p-4">Error loading records.</p>`;
  }
}

function loadMoreRecords() {
  state.recordsPage += 1;
  fetchRecords(true);
}

// Search Records lists every functionary type in one feed, but Supervisors
// carry a richer profile (circles + the full table of enumerators reporting
// to them) that only the dedicated /api/records/supervisor endpoint returns.
// The plain records-search payload used for the card itself doesn't include
// that, so clicking a Supervisor card here used to open the generic
// Enumerator modal with blank jurisdiction fields. Route Supervisor clicks
// to the same rich modal used on the Supervision tab instead, fetching the
// full detail on demand since it isn't preloaded on this page.
function openRecordProfile(userId) {
  const rec = (state.recordsCache || {})[userId];
  if (!rec) return;

  if (/supervisor/i.test(rec.role || "")) {
    openSupervisorProfileFromSearch(rec);
  } else {
    openEnumeratorModal(userId);
  }
}

async function openSupervisorProfileFromSearch(rec) {
  try {
    const res = await apiFetch(`/api/records/supervisor?q=${encodeURIComponent(rec.user_id)}`);
    const data = await res.json();
    const sup = (data.supervisors || []).find(s => s.user_id === rec.user_id) || (data.supervisors || [])[0];

    if (!sup) {
      // Fallback so a click never does nothing, even if the lookup misses.
      openEnumeratorModal(rec.user_id);
      return;
    }

    state.supervisorsCache = state.supervisorsCache || {};
    state.supervisorsCache[sup.name] = sup;
    openSupervisorModal(sup.name);
  } catch (err) {
    openEnumeratorModal(rec.user_id);
  }
}

function openEnumeratorModal(userId) {
  const rec = (state.recordsCache || {})[userId];
  if (!rec) return;

  const modal = document.getElementById("modal-enumerator-profile");
  if (!modal) return;

  const initials = rec.name
    ? rec.name.split(" ").filter(Boolean).slice(0, 2).map(p => p[0]).join("").toUpperCase()
    : "EN";
  document.getElementById("enum-modal-avatar").textContent = initials;
  document.getElementById("enum-modal-name").textContent = rec.name || "Unknown";
  document.getElementById("enum-modal-role").textContent = rec.role || "Enumerator";
  document.getElementById("enum-modal-id").textContent = rec.user_id || "N/A";

  const cleanMob = (rec.mobile || "8453441975").replace(/[^0-9]/g, "");
  const waMsg = `Inquiry regarding ${rec.name}${rec.hlb_number ? ` (HLB ${rec.hlb_number})` : ""}`;
  document.getElementById("enum-modal-phone").textContent = rec.mobile ? `+91 ${cleanMob}` : "Call";
  document.getElementById("enum-modal-call-btn").onclick = () => nativeCall(cleanMob);
  document.getElementById("enum-modal-wa-btn").onclick = () => nativeWhatsApp(`91${cleanMob}`, waMsg);

  // HLB/Circle/Supervisor only apply to individual block-level roles
  // (Enumerators) — hide that whole section for Supervisors/other roles
  // instead of showing a confusing row of dashes. An Enumerator with no
  // HLB match is a real gap (registered but not yet assigned a block),
  // so flag it clearly rather than blanking it.
  const isEnumeratorRole = /enumerator/i.test(rec.role || "");
  const allocationSection = document.getElementById("enum-modal-allocation-section");
  if (allocationSection) {
    allocationSection.classList.toggle("hidden", !isEnumeratorRole);
  }
  const hlbEl = document.getElementById("enum-modal-hlb");
  if (rec.hlb_number) {
    hlbEl.textContent = rec.hlb_number;
    hlbEl.classList.remove("text-amber-600");
  } else {
    hlbEl.textContent = "Unallocated";
    hlbEl.classList.add("text-amber-600");
  }
  document.getElementById("enum-modal-circle").textContent = rec.circle || "—";
  document.getElementById("enum-modal-supervisor").textContent = rec.supervisor || "—";
  document.getElementById("enum-modal-village").textContent = rec.village_town || rec.area_name || "—";
  document.getElementById("enum-modal-landmark").textContent = rec.landmark || "—";
  document.getElementById("enum-modal-boundary").textContent = rec.boundary_description || "No boundary description on record.";

  const mapsLink = document.getElementById("enum-modal-maps-link");
  if (rec.maps_url) {
    mapsLink.href = rec.maps_url;
    mapsLink.classList.remove("hidden");
  } else {
    mapsLink.classList.add("hidden");
  }

  document.getElementById("enum-modal-ask-ai-btn").onclick = () => {
    closeEnumeratorModal();
    quickAsk(`Show details for ${rec.name}`);
  };

  modal.classList.remove("hidden");
}

function closeEnumeratorModal() {
  const modal = document.getElementById("modal-enumerator-profile");
  if (modal) modal.classList.add("hidden");
}

// ==================== 7. MANUALS & GUIDELINES HANDLERS ====================
// manualTopicsCache holds, per indexed PDF, the distinct section/topic
// headers extracted during ingestion — [{source_file, doc_title, topics:[{section_header, page_number}]}]
// It backs both the page-level "Browse Topics" search box and the per-document
// topic list shown inside the manual detail modal.
let manualTopicsCache = [];

// Escapes a string for safe embedding inside a single-quoted JS string
// literal that itself sits inside a double-quoted HTML attribute (the
// pattern used by every dynamically-built onclick="fn('...')" below).
// escapeHtml() alone is NOT enough here — the browser decodes HTML entities
// in attribute values before treating them as JS, so an escaped apostrophe
// would still terminate the string early.
function jsAttr(str) {
  if (!str) return "";
  return String(str)
    .replace(/\\/g, "\\\\")
    .replace(/'/g, "\\'")
    .replace(/"/g, "&quot;")
    .replace(/\n/g, " ");
}

async function loadManualPage() {
  await Promise.all([loadManualDocs(), loadManualTopics()]);
}

async function loadManualDocs() {
  const container = document.getElementById("manual-doc-list");
  if (!container) return;
  try {
    const res = await apiFetch("/api/manuals/list");
    const data = await res.json();
    const docs = data.manuals || [];
    if (docs.length === 0) {
      container.innerHTML = `<p class="text-xs text-on-surface-variant col-span-full">No manuals uploaded yet.</p>`;
      return;
    }
    container.innerHTML = docs.map(doc => `
      <div onclick="openPdfModal('${jsAttr(doc.filename)}')"
        class="bg-surface-container-lowest border border-outline-variant/30 rounded-xl p-4 flex items-center justify-between gap-3 cursor-pointer hover:bg-surface-container-low hover:border-primary/40 transition-all active:scale-[0.99]">
        <div class="flex items-center gap-3 min-w-0">
          <span class="material-symbols-outlined text-error text-3xl shrink-0">picture_as_pdf</span>
          <div class="min-w-0">
            <h4 class="text-sm font-bold text-on-surface truncate">${escapeHtml(doc.title)}</h4>
            <p class="text-xs text-on-surface-variant">${doc.pages ? `${doc.pages} Pages • ` : ""}${doc.chunk_count} indexed section${doc.chunk_count === 1 ? "" : "s"} • ${escapeHtml(doc.size)}</p>
          </div>
        </div>
        <span class="material-symbols-outlined text-primary shrink-0">chevron_right</span>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<p class="text-xs text-error col-span-full">Could not load manuals.</p>`;
  }
}

async function loadManualTopics() {
  try {
    const res = await apiFetch("/api/manuals/topics");
    const data = await res.json();
    manualTopicsCache = data.documents || [];
  } catch (err) {
    manualTopicsCache = [];
  }
  renderManualTopics();
}

// Renders the "Browse Topics" chip list from the cached topic index,
// filtered client-side by the manual-topics-filter search box. Optionally
// scoped to one document's source_file (used inside the PDF detail modal).
function renderManualTopics(filterSourceFile = null) {
  const container = document.getElementById("manual-topics-list");
  if (!container) return;
  const filterInput = document.getElementById("manual-topics-filter");
  const q = (filterInput ? filterInput.value : "").trim().toLowerCase();

  let rows = [];
  manualTopicsCache.forEach(doc => {
    if (filterSourceFile && doc.source_file !== filterSourceFile) return;
    doc.topics.forEach(topic => {
      if (q && !topic.section_header.toLowerCase().includes(q)) return;
      rows.push({ ...topic, source_file: doc.source_file, doc_title: doc.doc_title });
    });
  });

  if (rows.length === 0) {
    container.innerHTML = `<p class="text-xs text-on-surface-variant">${q ? "No matching topics." : "No topics indexed yet."}</p>`;
    return;
  }

  container.innerHTML = rows.slice(0, 80).map(t => `
    <button onclick="viewManualTopic(${t.id}, '${jsAttr(t.section_header)}')"
      title="${escapeHtml(t.doc_title)} • Page ${t.page_number}"
      class="text-left text-xs bg-surface border border-outline-variant/30 hover:border-primary hover:text-primary rounded-full px-3.5 py-2 transition-colors">
      ${escapeHtml(t.section_header)}
    </button>
  `).join("");
}

// Loads the exact indexed chunk for one topic (clicked either from the
// page-level Browse Topics list or from inside a manual's detail modal),
// looked up by its row id — not by header text, since a topic's label can
// be a derived snippet rather than a real stored section_header — and
// surfaces it in the existing AI Synthesized Excerpt card.
async function viewManualTopic(chunkId, fallbackLabel) {
  const titleEl = document.getElementById("manual-answer-title");
  const bodyEl = document.getElementById("manual-answer-body");
  const sourceEl = document.getElementById("manual-answer-source");

  titleEl.textContent = fallbackLabel;
  bodyEl.textContent = "Loading topic content...";

  try {
    const res = await apiFetch(`/api/manuals/chunk?id=${encodeURIComponent(chunkId)}`);
    const data = await res.json();
    if (data.error) {
      bodyEl.textContent = "Could not load this topic.";
      return;
    }
    titleEl.textContent = data.section_header || fallbackLabel;
    bodyEl.textContent = data.chunk_text;
    sourceEl.innerHTML = `Source: <strong>${escapeHtml(data.doc_title)}, Page ${data.page_number}</strong>`;
  } catch (err) {
    bodyEl.textContent = "Error loading topic content.";
  }

  closePdfModal();
  const answerCard = document.getElementById("manual-ai-answer-card");
  if (answerCard) answerCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function executeManualSearch() {
  const query = document.getElementById("manual-search-input").value.trim();
  if (!query) return;

  const titleEl = document.getElementById("manual-answer-title");
  const bodyEl = document.getElementById("manual-answer-body");
  const sourceEl = document.getElementById("manual-answer-source");

  titleEl.textContent = `Searching: ${query}`;
  bodyEl.textContent = "Querying guideline manual indexes...";

  try {
    const res = await apiFetch(`/api/manuals/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    if (data.results && data.results.length > 0) {
      const best = data.results[0];
      titleEl.textContent = best.section_header || "Relevant Manual Guideline";
      bodyEl.textContent = best.chunk_text;
      sourceEl.innerHTML = `Source: <strong>${escapeHtml(best.doc_title)}, Page ${best.page_number}</strong>`;
    } else {
      titleEl.textContent = "No Exact Guideline Match";
      bodyEl.textContent = "Please consult the full manuals below or contact Technical Assistant Shahin Sha A. (+91 84534 41975).";
      sourceEl.innerHTML = "Source: Census Operating Manuals";
    }
  } catch (err) {
    bodyEl.textContent = "Error executing manual search.";
  }
}

// Opens the manual detail modal for one document — a real, working modal
// (the markup for #modal-pdf was previously missing from index.html
// entirely, so this call silently did nothing before). Shows a genuine link
// to open the actual PDF plus the real indexed topics for that file, in
// place of the old hardcoded "Sample Section Overview" placeholder text.
async function openPdfModal(filename) {
  const modal = document.getElementById("modal-pdf");
  const title = document.getElementById("pdf-modal-title");
  const content = document.getElementById("pdf-modal-content");
  if (!modal || !title || !content) return;

  const doc = manualTopicsCache.find(d => d.source_file === filename);
  const docTitle = (doc && doc.doc_title) || filename;
  title.textContent = docTitle;

  const fileUrl = `/api/manuals/file/${encodeURIComponent(filename)}`;
  const topics = doc ? doc.topics : [];

  content.innerHTML = `
    <div class="space-y-4">
      <div class="flex items-center gap-3 p-3 bg-primary-fixed/20 rounded-lg text-primary text-xs font-semibold">
        <span class="material-symbols-outlined">info</span>
        <span>Offline Indexed Document • Full-Text Search Enabled</span>
      </div>
      <a href="${fileUrl}" target="_blank" rel="noopener"
        class="w-full py-2.5 bg-primary text-white text-xs font-semibold rounded-full hover:bg-primary-container transition-all flex items-center justify-center gap-1.5">
        <span class="material-symbols-outlined text-base">open_in_new</span>
        Open Full PDF
      </a>
      <div>
        <p class="text-xs font-bold text-on-surface mb-2">Topics in this document (${topics.length})</p>
        <div class="flex flex-wrap gap-2 max-h-56 overflow-y-auto pr-1">
          ${topics.length === 0
            ? `<p class="text-xs text-on-surface-variant">No indexed topics found for this file yet.</p>`
            : topics.map(t => `
              <button onclick="viewManualTopic(${t.id}, '${jsAttr(t.section_header)}')"
                class="text-left text-xs bg-surface border border-outline-variant/30 hover:border-primary hover:text-primary rounded-full px-3.5 py-2 transition-colors">
                ${escapeHtml(t.section_header)}
              </button>
            `).join("")}
        </div>
      </div>
      <button onclick="closePdfModal(); quickAsk('What are the key instructions in ${jsAttr(docTitle)}?')" class="w-full py-2.5 border border-primary text-primary text-xs font-semibold rounded-full hover:bg-primary-fixed transition-all">
        Ask AI to Summarize this Document
      </button>
    </div>
  `;
  modal.classList.remove("hidden");
}

function closePdfModal() {
  const modal = document.getElementById("modal-pdf");
  if (modal) modal.classList.add("hidden");
}

// ==================== 8. NOTIFICATIONS & UPDATES ====================
async function loadNotifications(category = "All") {
  const container = document.getElementById("notifications-list");
  if (!container) return;

  try {
    const res = await apiFetch(`/api/notifications?category=${category}`);
    const data = await res.json();
    container.innerHTML = "";

    if (!data.notifications || data.notifications.length === 0) {
      container.innerHTML = `<p class="text-xs text-on-surface-variant p-4">No notifications in this category.</p>`;
      return;
    }

    data.notifications.forEach(item => {
      const isUrgent = item.priority === "urgent";
      const icon = isUrgent ? "warning" : (item.category === "Alerts" ? "database" : "policy");
      const iconBg = isUrgent ? "bg-error-container text-on-error-container" : (item.category === "Alerts" ? "bg-tertiary-container text-white" : "bg-primary-container text-white");

      const itemDiv = document.createElement("div");
      itemDiv.className = "relative group cursor-pointer animate-fade-in";
      itemDiv.innerHTML = `
        <div class="absolute -left-[35px] md:-left-[43px] top-1 bg-surface rounded-full p-1 border-2 border-surface-variant group-hover:border-primary transition-colors">
          <div class="${iconBg} w-8 h-8 rounded-full flex items-center justify-center">
            <span class="material-symbols-outlined text-[18px]" style="font-variation-settings: 'FILL' 1;">${icon}</span>
          </div>
        </div>
        <div class="bg-surface-container-lowest border ${isUrgent ? 'border-error-container' : 'border-outline-variant/30'} rounded-xl p-4 shadow-sm hover:shadow-md transition-all">
          <div class="flex justify-between items-start mb-1.5">
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-bold text-on-surface">${escapeHtml(item.title)}</h3>
              ${isUrgent ? '<span class="bg-error text-white text-[10px] font-bold px-2 py-0.5 rounded-full">Urgent</span>' : ''}
            </div>
            <span class="text-[11px] text-on-surface-variant whitespace-nowrap ml-2">${escapeHtml(item.timestamp_str || 'Recent')}</span>
          </div>
          <p class="text-xs text-on-surface-variant leading-relaxed">${escapeHtml(item.content)}</p>
        </div>
      `;
      container.appendChild(itemDiv);
    });
  } catch (err) {
    container.innerHTML = `<p class="text-xs text-error">Could not load updates.</p>`;
  }
}

function filterNotifications(cat) {
  ["all", "alerts", "notices"].forEach(c => {
    const btn = document.getElementById(`tab-notif-${c}`);
    if (btn) {
      if (c.toLowerCase() === cat.toLowerCase()) {
        btn.className = "px-4 py-1.5 rounded-full bg-primary text-white text-xs font-semibold transition-all";
      } else {
        btn.className = "px-4 py-1.5 rounded-full border border-outline text-on-surface text-xs font-semibold hover:bg-surface-container transition-all";
      }
    }
  });
  loadNotifications(cat);
}

// ==================== 8b. ADMIN: ALERTS & NOTICES MANAGEMENT ====================
// Feature requested alongside the admin-portal lockdown: Technical Assistant
// admins can broadcast new alerts/notices and remove old ones. Regular
// guest/field-functionary sessions never reach this UI (admin nav is
// hidden for them, see applyRoleBasedNav()) and the backend independently
// enforces this via _require_admin() on the POST/DELETE routes.
async function loadAdminNotices() {
  const container = document.getElementById("admin-notices-list");
  if (!container) return;

  container.innerHTML = `<div class="flex justify-center p-4"><div class="loader-spinner-primary"></div></div>`;

  try {
    const res = await apiFetch("/api/notifications?category=All");
    const data = await res.json();
    container.innerHTML = "";

    if (!data.notifications || data.notifications.length === 0) {
      container.innerHTML = `<p class="text-xs text-on-surface-variant p-4">No alerts or notices yet. Create one above.</p>`;
      return;
    }

    data.notifications.forEach(item => {
      const row = document.createElement("div");
      row.className = "flex items-start justify-between gap-3 p-3 rounded-lg border border-outline-variant/30 bg-surface";
      row.innerHTML = `
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <h4 class="text-xs font-bold text-on-surface">${escapeHtml(item.title)}</h4>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-surface-container text-on-surface-variant font-semibold uppercase">${escapeHtml(item.category)}</span>
            ${item.priority === "urgent" ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-error text-white font-semibold">Urgent</span>' : ''}
          </div>
          <p class="text-[11px] text-on-surface-variant mt-1 truncate">${escapeHtml(item.content)}</p>
        </div>
        <button onclick="handleDeleteNotice(${item.id})" title="Delete" class="shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-error hover:bg-error-container/40 transition-colors">
          <span class="material-symbols-outlined text-lg">delete</span>
        </button>
      `;
      container.appendChild(row);
    });
  } catch (err) {
    container.innerHTML = `<p class="text-xs text-error p-4">Could not load alerts/notices.</p>`;
  }
}

async function handleCreateNotice(e) {
  e.preventDefault();
  const title = document.getElementById("notice-title-input").value.trim();
  const content = document.getElementById("notice-content-input").value.trim();
  const category = document.getElementById("notice-category-select").value;
  const priority = document.getElementById("notice-priority-select").value;

  if (!title || !content) {
    showToast("Title and content are required.");
    return;
  }

  try {
    const res = await apiFetch("/api/notifications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content, category, priority, badge: priority === "urgent" ? "Urgent" : "New" })
    });
    const data = await res.json();
    if (data.success) {
      showToast("Alert/Notice broadcasted successfully.");
      document.getElementById("notice-title-input").value = "";
      document.getElementById("notice-content-input").value = "";
      loadAdminNotices();
      loadNotifications();
    } else {
      showToast(data.error || "Failed to broadcast.");
    }
  } catch (err) {
    showToast("Network error broadcasting notice.");
  }
}

async function handleDeleteNotice(id) {
  try {
    const res = await apiFetch(`/api/notifications/${id}`, { method: "DELETE" });
    const data = await res.json();
    if (data.success) {
      showToast("Notice deleted.");
      loadAdminNotices();
      loadNotifications();
    } else {
      showToast(data.error || "Failed to delete notice.");
    }
  } catch (err) {
    showToast("Network error deleting notice.");
  }
}

// ==================== 8c. SUPERVISOR LIST ====================
// Fetches the real, searchable list of supervisors (cross-referenced from all 3
// Excel sheets) from /api/records/supervisor with their complete list of assigned enumerators.
async function loadSupervisors() {
  const container = document.getElementById("supervisors-list");
  if (!container) return;
  const q = (document.getElementById("supervisor-search-input") || {}).value || "";

  container.innerHTML = `<div class="flex justify-center p-8"><div class="loader-spinner-primary"></div></div>`;
  state.supervisorsCache = {};

  try {
    const res = await apiFetch(`/api/records/supervisor?q=${encodeURIComponent(q.trim())}`);
    const data = await res.json();
    container.innerHTML = "";

    // Render the two Technical Assistants at the top — they are always
    // reachable regardless of search, since they support every circle.
    const taContainer = document.getElementById("supervisor-tech-assistants");
    if (taContainer && data.technical_assistants) {
      taContainer.innerHTML = data.technical_assistants.map(ta => {
        const initials = ta.name ? ta.name.split(" ").filter(Boolean).slice(0, 2).map(p => p[0]).join("").toUpperCase() : "TA";
        const avatarHtml = ta.photo
          ? `<img src="${escapeAttr(ta.photo)}" alt="${escapeAttr(ta.name)}" class="w-11 h-11 rounded-full object-cover shrink-0 border border-outline-variant/30">`
          : `<div class="w-11 h-11 rounded-full bg-primary-container text-white flex items-center justify-center text-sm font-bold shrink-0">${initials}</div>`;
        return `
        <div class="bg-surface-container-lowest border border-outline-variant/30 rounded-xl p-4 flex items-center justify-between gap-3">
          <div class="flex items-center gap-3 min-w-0">
            ${avatarHtml}
            <div class="min-w-0">
              <p class="text-sm font-bold text-on-surface truncate">${escapeHtml(ta.name)}</p>
              <p class="text-[11px] text-tertiary-container font-semibold uppercase tracking-wide">${escapeHtml(ta.designation)}</p>
              <p class="text-xs text-on-surface-variant mt-0.5">${escapeHtml(ta.phone)}</p>
            </div>
          </div>
          <a href="${escapeAttr(ta.whatsapp_link)}" target="_blank" rel="noopener noreferrer" class="w-9 h-9 rounded-full bg-[#25D366] text-white flex items-center justify-center shrink-0" title="WhatsApp">
            <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 1;">chat</span>
          </a>
        </div>
      `;
      }).join("");
    }

    if (!data.supervisors || data.supervisors.length === 0) {
      container.innerHTML = `
        <div class="bg-surface-container-lowest border border-outline-variant/30 rounded-2xl p-8 text-center text-on-surface-variant">
          <span class="material-symbols-outlined text-4xl text-outline mb-2">search_off</span>
          <p class="text-sm font-semibold">No supervisors found matching your search.</p>
        </div>
      `;
      return;
    }

    state.supervisorsCache = state.supervisorsCache || {};

    data.supervisors.forEach(sup => {
      state.supervisorsCache[sup.name] = sup;
      const cleanMob = (sup.mobile || "").replace(/[^0-9]/g, "");
      const initials = sup.name ? sup.name.split(" ").filter(Boolean).slice(0, 2).map(p => p[0]).join("").toUpperCase() : "SU";
      const circlesHtml = (sup.circles || []).filter(Boolean).map(c =>
        `<span class="px-2.5 py-1 bg-surface-variant text-on-surface rounded-md text-xs font-semibold border border-outline-variant/40">Circle ${escapeHtml(c)}</span>`
      ).join("") || `<span class="text-xs text-on-surface-variant">No circle on record</span>`;
      
      const card = document.createElement("div");
      card.className = "bg-surface-container-lowest rounded-2xl shadow-sm border border-outline-variant/30 overflow-hidden hover:shadow-md transition-all cursor-pointer group";
      card.onclick = () => openSupervisorModal(sup.name);

      card.innerHTML = `
        <div class="p-5 flex flex-col sm:flex-row sm:items-center gap-4">
          <div class="w-16 h-16 rounded-full bg-primary-container text-white flex items-center justify-center text-xl font-bold shrink-0">${escapeHtml(initials)}</div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <h3 class="text-lg font-bold text-on-surface group-hover:text-primary transition-colors truncate">${escapeHtml(sup.name)}</h3>
              <span class="text-[10px] px-2 py-0.5 rounded bg-tertiary-fixed text-tertiary-container font-semibold">Charge Supervisor</span>
            </div>
            <p class="text-xs text-on-surface-variant mt-0.5">${escapeHtml(sup.mobile || "No mobile on record")} • ID: <code class="font-mono">${escapeHtml(sup.user_id)}</code></p>
            <p class="text-xs text-on-surface-variant mt-0.5 font-medium">
              <span class="text-primary font-bold">${sup.hlb_count} Enumerator${sup.hlb_count === 1 ? "" : "s"}</span> Reporting under this Supervisor
              ${sup.area_name ? " • " + escapeHtml(sup.area_name) : ""}
            </p>
            <div class="flex flex-wrap gap-1.5 mt-2">${circlesHtml}</div>
          </div>
        </div>
        <div class="px-5 pb-5 flex flex-col sm:flex-row gap-2">
          ${cleanMob ? `
          <a href="https://wa.me/91${escapeAttr(cleanMob)}?text=${encodeURIComponent('Hello ' + sup.name + ', I am reaching out regarding HLB operations.')}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation();"
            class="flex-1 bg-[#25D366]/10 text-[#25D366] border border-[#25D366]/30 h-11 rounded-full font-semibold text-xs flex items-center justify-center gap-2 hover:bg-[#25D366] hover:text-white transition-all active:scale-95">
            <span class="material-symbols-outlined text-lg">chat</span><span>WhatsApp Supervisor</span>
          </a>` : ""}
          <button onclick="event.stopPropagation(); openSupervisorModal('${escapeAttr(sup.name)}')"
            class="flex-1 bg-primary text-white h-11 rounded-full font-semibold text-xs flex items-center justify-center gap-2 hover:bg-primary-container transition-all active:scale-95 shadow-sm">
            <span class="material-symbols-outlined text-lg">group</span><span>View All Assigned Enumerators (${sup.hlb_count})</span>
          </button>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `<p class="text-xs text-error p-4">Error loading supervisors.</p>`;
  }
}

function openSupervisorModal(supName) {
  const sup = (state.supervisorsCache || {})[supName];
  if (!sup) return;

  const modal = document.getElementById("modal-supervisor-profile");
  if (!modal) return;

  const initials = sup.name ? sup.name.split(" ").filter(Boolean).slice(0, 2).map(p => p[0]).join("").toUpperCase() : "SU";
  document.getElementById("sup-modal-avatar").textContent = initials;
  document.getElementById("sup-modal-name").textContent = sup.name;
  document.getElementById("sup-modal-id").textContent = sup.user_id || "N/A";
  document.getElementById("sup-modal-phone").textContent = sup.mobile ? `+91 ${sup.mobile}` : "No mobile on record";

  const circlesContainer = document.getElementById("sup-modal-circles");
  if (circlesContainer) {
    circlesContainer.innerHTML = (sup.circles || []).map(c => 
      `<span class="px-2 py-0.5 rounded bg-primary text-white text-[11px] font-bold">Circle ${escapeHtml(c)}</span>`
    ).join("") || `<span class="text-on-surface-variant text-xs">All Lakhipur</span>`;
  }

  document.getElementById("sup-modal-count").textContent = (sup.enumerators || []).length;

  const tableBody = document.getElementById("sup-modal-enum-table");
  if (tableBody) {
    tableBody.innerHTML = "";
    if (!sup.enumerators || sup.enumerators.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-on-surface-variant">No enumerators assigned to this supervisor in records.</td></tr>`;
    } else {
      sup.enumerators.forEach(e => {
        const cleanMob = (e.mobile || "").replace(/[^0-9]/g, "");
        const tr = document.createElement("tr");
        tr.className = "hover:bg-surface-container-low transition-colors";
        tr.innerHTML = `
          <td class="p-2.5 font-mono font-bold text-primary text-[11px]">HLB ${escapeHtml(e.hlb_no)}</td>
          <td class="p-2.5">
            <p class="font-bold text-on-surface">${escapeHtml(e.enumerator_name)}</p>
            <p class="text-[10px] text-on-surface-variant font-mono">${escapeHtml(e.enumerator_user_id)}</p>
          </td>
          <td class="p-2.5 text-on-surface-variant whitespace-nowrap">${escapeHtml(e.mobile || "—")}</td>
          <td class="p-2.5">
            <p class="font-medium text-on-surface text-[11px]">${escapeHtml(e.village_ward_name || e.area_name || "Lakhipur")}</p>
            ${e.landmark ? `<p class="text-[10px] text-on-surface-variant">Near: ${escapeHtml(e.landmark)}</p>` : ""}
          </td>
          <td class="p-2.5 text-right whitespace-nowrap">
            <div class="flex items-center justify-end gap-1.5">
              ${e.maps_url ? `
                <a href="${escapeAttr(e.maps_url)}" target="_blank" rel="noopener noreferrer" class="w-7 h-7 rounded-full bg-primary/10 text-primary flex items-center justify-center hover:bg-primary hover:text-white transition-colors" title="View Map">
                  <span class="material-symbols-outlined text-[15px]">map</span>
                </a>` : ""}
              ${cleanMob ? `
                <button onclick="nativeCall('${escapeAttr(cleanMob)}')" class="w-7 h-7 rounded-full bg-surface-container flex items-center justify-center text-primary hover:bg-primary hover:text-white transition-colors" title="Call">
                  <span class="material-symbols-outlined text-[15px]">call</span>
                </button>
                <button onclick="nativeWhatsApp('91${escapeAttr(cleanMob)}', 'Inquiry regarding HLB ${escapeAttr(e.hlb_no)} operations')" class="w-7 h-7 rounded-full bg-[#25D366]/10 text-[#25D366] flex items-center justify-center hover:bg-[#25D366] hover:text-white transition-colors" title="WhatsApp">
                  <span class="material-symbols-outlined text-[15px]">chat</span>
                </button>` : ""}
              <button onclick="closeSupervisorModal(); quickAsk('Show details for ${escapeAttr(e.enumerator_name)}')" class="w-7 h-7 rounded-full bg-primary text-white flex items-center justify-center hover:bg-primary-container transition-colors" title="Ask AI">
                <span class="material-symbols-outlined text-[14px]">smart_toy</span>
              </button>
            </div>
          </td>
        `;
        tableBody.appendChild(tr);
      });
    }
  }

  modal.classList.remove("hidden");
}

function closeSupervisorModal() {
  const modal = document.getElementById("modal-supervisor-profile");
  if (modal) modal.classList.add("hidden");
}

function debounceSupervisorSearch() {
  clearTimeout(state.searchDebounceTimer);
  state.searchDebounceTimer = setTimeout(loadSupervisors, 300);
}

// ==================== 9. ADMIN PANEL & FILE UPLOADERS ====================
async function loadAdminStats() {
  try {
    const res = await apiFetch("/api/admin/stats");
    const data = await res.json();
    
    const recEl = document.getElementById("stat-total-records");
    const queryEl = document.getElementById("stat-ai-queries");
    const chunksEl = document.getElementById("stat-manual-chunks");
    const latEl = document.getElementById("stat-latency");
    const syncEl = document.getElementById("stat-last-sync");

    if (recEl) recEl.textContent = (data.total_records || 1488).toLocaleString();
    if (queryEl) queryEl.textContent = (data.ai_queries_count || 54012).toLocaleString();
    if (chunksEl) chunksEl.textContent = (data.manual_chunks_count || 43).toLocaleString();
    if (latEl) latEl.textContent = `Avg response: ${data.avg_latency || '1.2s'}`;
    if (syncEl) syncEl.textContent = `Last sync: ${data.last_sync || 'Just now'}`;
  } catch (err) {
    console.log("Stats fetch error:", err);
  }
}

async function triggerForceSync() {
  showToast("Re-indexing knowledge base from Excel and PDF manuals...");
  try {
    const res = await apiFetch("/api/admin/force-sync", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      showToast("Knowledge base re-indexed successfully!");
      loadAdminStats();
      loadUploadedFiles();
    } else {
      showToast(data.error || "Sync failed.");
    }
  } catch (err) {
    showToast("Force sync network request failed.");
  }
}

/**
 * Uploads a file with real upload progress. fetch() has no way to observe
 * upload progress (only download/response progress), so this uses
 * XMLHttpRequest directly — the only browser API that exposes
 * xhr.upload.onprogress — to drive the Admin Panel's progress bars.
 * Returns a Promise resolving to the parsed JSON body on any HTTP response
 * (mirrors apiFetch + res.json(), so callers still check data.success),
 * and rejecting only on a genuine network failure.
 */
function uploadFileWithProgress(path, file, onProgress) {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", getApiBase() + path, true);
    if (state.authToken) {
      xhr.setRequestHeader("Authorization", `Bearer ${state.authToken}`);
    }

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      let data;
      try {
        data = JSON.parse(xhr.responseText);
      } catch (err) {
        reject(new Error("Invalid server response."));
        return;
      }
      resolve(data);
    };
    xhr.onerror = () => reject(new Error("Network error during upload."));
    xhr.send(formData);
  });
}

function setUploadProgressUi(kind, { visible, pct = 0, label = "Uploading..." } = {}) {
  const wrap = document.getElementById(`${kind}-upload-progress-wrap`);
  const bar = document.getElementById(`${kind}-upload-progress-bar`);
  const pctEl = document.getElementById(`${kind}-upload-progress-pct`);
  const labelEl = document.getElementById(`${kind}-upload-progress-label`);
  const dropzone = document.getElementById(`${kind}-upload-dropzone`);

  if (wrap) wrap.classList.toggle("hidden", !visible);
  if (bar) bar.style.width = `${pct}%`;
  if (pctEl) pctEl.textContent = `${pct}%`;
  if (labelEl) labelEl.textContent = label;
  // Block re-triggering a second upload (and dim the dropzone) while one is in flight.
  if (dropzone) {
    dropzone.classList.toggle("opacity-50", visible);
    dropzone.classList.toggle("pointer-events-none", visible);
  }
}

async function handleExcelUpload(input) {
  const file = input.files[0];
  if (!file) return;

  setUploadProgressUi("excel", { visible: true, pct: 0, label: `Uploading ${file.name}...` });
  try {
    const data = await uploadFileWithProgress("/api/admin/upload-excel", file, (pct) => {
      setUploadProgressUi("excel", { visible: true, pct, label: `Uploading ${file.name}...` });
    });
    if (data.success) {
      setUploadProgressUi("excel", { visible: true, pct: 100, label: "Processing..." });
      showToast(data.message);
      loadAdminStats();
      loadUploadedFiles();
    } else {
      showToast(data.error || "Upload failed.");
    }
  } catch (err) {
    showToast("Excel upload failed.");
  } finally {
    setTimeout(() => setUploadProgressUi("excel", { visible: false }), 600);
  }
  input.value = "";
}

async function handlePdfUpload(input) {
  const file = input.files[0];
  if (!file) return;

  setUploadProgressUi("pdf", { visible: true, pct: 0, label: `Uploading ${file.name}...` });
  try {
    const data = await uploadFileWithProgress("/api/admin/upload-pdf", file, (pct) => {
      setUploadProgressUi("pdf", { visible: true, pct, label: `Uploading ${file.name}...` });
    });
    if (data.success) {
      setUploadProgressUi("pdf", { visible: true, pct: 100, label: "Chunking & indexing..." });
      showToast(data.message);
      loadAdminStats();
      loadUploadedFiles();
    } else {
      showToast(data.error || "Upload failed.");
    }
  } catch (err) {
    showToast("PDF upload failed.");
  } finally {
    setTimeout(() => setUploadProgressUi("pdf", { visible: false }), 600);
  }
  input.value = "";
}

async function loadUploadedFiles() {
  const container = document.getElementById("admin-uploaded-files-list");
  if (!container) return;

  try {
    const res = await apiFetch("/api/admin/uploaded-files");
    const data = await res.json();
    container.innerHTML = "";

    if (!data.files || data.files.length === 0) {
      container.innerHTML = `<p class="text-xs text-on-surface-variant p-3 text-center">No source files detected.</p>`;
      return;
    }

    data.files.forEach(f => {
      const isPdf = f.filename.endsWith(".pdf");
      const icon = isPdf ? "picture_as_pdf" : "table_view";
      const iconColor = isPdf ? "text-error" : "text-primary";
      
      const item = document.createElement("div");
      item.className = "flex items-center justify-between p-3 rounded-lg border border-outline-variant/30 bg-surface hover:bg-surface-container-low transition-colors";
      item.innerHTML = `
        <div class="flex items-center gap-3 min-w-0">
          <span class="material-symbols-outlined ${iconColor} text-2xl shrink-0">${icon}</span>
          <div class="truncate">
            <p class="text-xs font-bold text-on-surface truncate">${escapeHtml(f.filename)}</p>
            <p class="text-[11px] text-on-surface-variant">${escapeHtml(f.file_type)} • ${escapeHtml(f.size_str)} • Modified ${escapeHtml(f.last_modified)}</p>
          </div>
        </div>
        <div class="flex items-center gap-1.5 shrink-0">
          <button onclick="handleDeleteUploadedFile('${escapeAttr(f.filename)}')" title="Delete File"
            class="w-8 h-8 rounded-full flex items-center justify-center text-error hover:bg-error-container/40 transition-colors">
            <span class="material-symbols-outlined text-base">delete</span>
          </button>
        </div>
      `;
      container.appendChild(item);
    });
  } catch (err) {
    container.innerHTML = `<p class="text-xs text-error p-3">Failed to load repository files.</p>`;
  }
}

async function handleDeleteUploadedFile(filename) {
  if (!confirm(`Are you sure you want to delete '${filename}'? This will update the knowledge base.`)) {
    return;
  }
  showToast(`Deleting ${filename}...`);
  try {
    const res = await apiFetch(`/api/admin/uploaded-files/${encodeURIComponent(filename)}`, {
      method: "DELETE"
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message || "File deleted.");
      loadUploadedFiles();
      loadAdminStats();
    } else {
      showToast(data.error || "Could not delete file.");
    }
  } catch (err) {
    showToast("Network error deleting file.");
  }
}

async function loadAdminUsers(q = "") {
  const tbody = document.getElementById("admin-users-table-body");
  if (!tbody) return;

  try {
    const res = await apiFetch(`/api/admin/users?q=${encodeURIComponent(q)}&limit=15`);
    const data = await res.json();
    tbody.innerHTML = "";

    if (!data.users || data.users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-on-surface-variant">No functionaries found matching search.</td></tr>`;
      return;
    }

    data.users.forEach(u => {
      const isActive = u.status === "ACTIVE";
      const statusBadge = isActive
        ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#2e7d32]/10 text-[#2e7d32]">Active</span>`
        : `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-error/10 text-error">Disabled</span>`;

      const tr = document.createElement("tr");
      tr.className = "hover:bg-surface-container-low transition-colors";
      tr.innerHTML = `
        <td class="p-3 font-mono font-bold text-[11px] text-primary">${escapeHtml(u.user_id)}</td>
        <td class="p-3 font-bold text-on-surface">${escapeHtml(u.name)}</td>
        <td class="p-3 text-on-surface-variant">${escapeHtml(u.functionary_type || 'Enumerator')}</td>
        <td class="p-3 text-on-surface-variant">${escapeHtml(u.mobile_number || '—')}</td>
        <td class="p-3 text-on-surface-variant">${escapeHtml(u.sub_district || u.district || 'Lakhipur')}</td>
        <td class="p-3">${statusBadge}</td>
        <td class="p-3 text-right">
          <button onclick="handleToggleUserStatus('${escapeAttr(u.user_id)}')"
            class="text-[11px] font-semibold px-2.5 py-1 rounded border ${isActive ? 'border-error/40 text-error hover:bg-error-container/30' : 'border-[#2e7d32]/40 text-[#2e7d32] hover:bg-[#2e7d32]/10'} transition-all">
            ${isActive ? 'Disable' : 'Activate'}
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-error">Error loading user records.</td></tr>`;
  }
}

function debounceAdminUserSearch() {
  clearTimeout(state.searchDebounceTimer);
  state.searchDebounceTimer = setTimeout(() => {
    const q = (document.getElementById("admin-user-search-input") || {}).value || "";
    loadAdminUsers(q.trim());
  }, 300);
}

async function handleToggleUserStatus(userId) {
  try {
    const res = await apiFetch(`/api/admin/users/${encodeURIComponent(userId)}/toggle-status`, {
      method: "POST"
    });
    const data = await res.json();
    if (data.success) {
      showToast(`User ${userId} status changed to ${data.new_status}`);
      const q = (document.getElementById("admin-user-search-input") || {}).value || "";
      loadAdminUsers(q.trim());
    } else {
      showToast(data.error || "Failed to update user status.");
    }
  } catch (err) {
    showToast("Network error updating status.");
  }
}

async function loadAdminQueryLogs() {
  const container = document.getElementById("admin-query-logs-list");
  if (!container) return;

  try {
    const res = await apiFetch("/api/admin/query-logs?limit=20");
    const data = await res.json();
    container.innerHTML = "";

    if (!data.query_logs || data.query_logs.length === 0) {
      container.innerHTML = `<p class="text-xs text-on-surface-variant p-3 text-center">No AI queries logged yet.</p>`;
      return;
    }

    data.query_logs.forEach(log => {
      const item = document.createElement("div");
      item.className = "p-3 rounded-lg border border-outline-variant/30 bg-surface flex flex-col gap-1";
      item.innerHTML = `
        <div class="flex items-center justify-between gap-2">
          <span class="text-xs font-bold text-on-surface truncate">"${escapeHtml(log.query_text)}"</span>
          <span class="text-[10px] text-on-surface-variant shrink-0">${escapeHtml(log.timestamp || 'Recent')}</span>
        </div>
        <div class="flex items-center gap-2 text-[10px] text-on-surface-variant">
          <span class="px-1.5 py-0.5 rounded bg-primary-fixed text-primary font-semibold">${escapeHtml(log.source_tag || 'AI Chat')}</span>
          <span>User: <code class="font-mono">${escapeHtml(log.user_id || 'anonymous')}</code></span>
        </div>
      `;
      container.appendChild(item);
    });
  } catch (err) {
    container.innerHTML = `<p class="text-xs text-error p-3">Failed to load query logs.</p>`;
  }
}

// ==================== 9a. ADMIN: AI STATUS & ACCOUNT SUPPORT ====================

/**
 * Show whether the assistant can reach a language model. This is the panel
 * that makes the single most common failure visible: with no GEMINI_API_KEY
 * set on the server, every question silently falls back to records-and-
 * manuals-only answers, which looks like the AI is restricted to the PDFs.
 */
async function loadAiStatus(probe = false) {
  const box = document.getElementById("admin-ai-status");
  if (!box) return;
  box.innerHTML = `<div class="flex justify-center p-2"><div class="loader-spinner-primary"></div></div>`;

  try {
    const res = await apiFetch(`/api/admin/ai-status${probe ? "?probe=1" : ""}`);
    const data = await res.json();
    if (!data.success) {
      box.innerHTML = `<p class="text-xs text-error">${escapeHtml(data.error || "Could not read AI status.")}</p>`;
      return;
    }

    const ai = data.ai;
    const healthy = ai.mode === "llm";
    const tone = healthy
      ? { chip: "bg-[#2e7d32]/10 text-[#2e7d32]", icon: "check_circle", iconClass: "text-[#2e7d32]", label: "Full AI answers" }
      : { chip: "bg-error/10 text-error", icon: "error", iconClass: "text-error", label: "Records & manuals only" };

    const rows = [
      ["Provider", ai.provider],
      ["Model", ai.model],
      ["API key configured", ai.configured ? "Yes" : "No"],
      ["Daily web-search limit", `${ai.daily_web_search_limit} per user`],
    ];
    if (ai.reachable !== undefined) rows.push(["Reachable from server", ai.reachable ? "Yes" : "No"]);
    if (ai.http_status) rows.push(["Last HTTP status", ai.http_status]);
    if (ai.last_error) rows.push(["Last error", `${ai.last_error_kind || ""} — ${ai.last_error}`]);
    if (ai.last_error_at) rows.push(["Last error at", ai.last_error_at]);

    box.innerHTML = `
      <div class="flex items-start gap-3 mb-3">
        <span class="material-symbols-outlined ${tone.iconClass} mt-0.5">${tone.icon}</span>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${tone.chip}">${tone.label}</span>
          </div>
          <p class="text-xs text-on-surface-variant mt-1.5 leading-relaxed">${escapeHtml(ai.summary || "")}</p>
        </div>
      </div>
      <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 text-[11px]">
        ${rows.map(([k, v]) => `
          <div class="flex justify-between gap-3 border-b border-outline-variant/20 py-1">
            <dt class="text-on-surface-variant shrink-0">${escapeHtml(k)}</dt>
            <dd class="text-on-surface font-medium text-right break-all">${escapeHtml(String(v))}</dd>
          </div>`).join("")}
      </dl>
      ${healthy ? "" : `
        <div class="mt-3 p-3 rounded-lg bg-surface-container text-[11px] text-on-surface-variant leading-relaxed">
          <strong class="text-on-surface">To enable full AI answers:</strong> set <code class="font-mono">GEMINI_API_KEY</code>
          in the PythonAnywhere web app's environment variables, then reload the web app. A free key can be
          created at Google AI Studio. On a free PythonAnywhere account, outbound access is allowlist-only —
          if the key is set but still unreachable, set
          <code class="font-mono">OUTBOUND_HTTP_PROXY=http://proxy.server:3128</code> as well.
        </div>`}
    `;
  } catch (err) {
    box.innerHTML = `<p class="text-xs text-error">Could not read AI status.</p>`;
  }
}

async function handleAdminResetPassword() {
  const identifier = (document.getElementById("support-identifier").value || "").trim();
  const box = document.getElementById("support-result");
  if (!identifier) return showToast("Enter the user's mobile number or username.");

  try {
    const res = await apiFetch("/api/admin/users/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier })
    });
    const data = await res.json();

    if (!data.success) {
      box.className = "rounded-xl border border-error/40 bg-error/5 p-4";
      box.innerHTML = `<p class="text-sm text-error font-medium">${escapeHtml(data.message || "Could not issue a password.")}</p>`;
      box.classList.remove("hidden");
      return;
    }

    box.className = "rounded-xl border border-[#2e7d32]/40 bg-[#2e7d32]/5 p-4";
    box.innerHTML = `
      <p class="text-sm font-bold text-on-surface">${escapeHtml(data.name)}</p>
      <p class="text-xs text-on-surface-variant mb-2">${escapeHtml(data.account)}</p>
      <p class="text-xs text-on-surface-variant mb-1">Read this out to the user:</p>
      <div class="flex items-center gap-2">
        <code class="flex-1 px-3 py-2 rounded-lg bg-surface border border-outline-variant font-mono text-base font-bold tracking-widest text-on-surface">${escapeHtml(data.temporary_password)}</code>
        <button onclick="copyTemporaryPassword('${escapeAttr(data.temporary_password)}')"
          class="shrink-0 px-3 py-2 text-xs font-semibold text-primary rounded-full border border-primary/40 hover:bg-primary-fixed/40 transition-colors">Copy</button>
      </div>
      <p class="text-[11px] text-on-surface-variant mt-2 leading-relaxed">${escapeHtml(data.note)}
      This is shown once and is not stored anywhere in readable form.</p>`;
    box.classList.remove("hidden");
    loadAdminAccounts();
    loadAuthAudit();
  } catch (err) {
    showToast("Could not issue a temporary password.");
  }
}

function copyTemporaryPassword(value) {
  navigator.clipboard.writeText(value).then(
    () => showToast("Temporary password copied."),
    () => showToast("Could not copy — please read it from the screen.")
  );
}

async function handleAdminUnlock() {
  const identifier = (document.getElementById("support-identifier").value || "").trim();
  if (!identifier) return showToast("Enter the user's mobile number or username.");
  try {
    const res = await apiFetch("/api/admin/users/unlock", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier })
    });
    const data = await res.json();
    showToast(data.message || (data.success ? "Account unlocked." : "Could not unlock."));
    if (data.success) loadAdminAccounts();
  } catch (err) {
    showToast("Could not unlock the account.");
  }
}

async function loadAdminAccounts() {
  const tbody = document.getElementById("admin-accounts-body");
  if (!tbody) return;
  try {
    const res = await apiFetch("/api/admin/accounts");
    const data = await res.json();
    if (!data.success) {
      tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-error">Could not load accounts.</td></tr>`;
      return;
    }
    if (!data.accounts.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-on-surface-variant">No password accounts registered yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    data.accounts.forEach(a => {
      let stateChip = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#2e7d32]/10 text-[#2e7d32]">Active</span>`;
      if (a.locked) {
        stateChip = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-error/10 text-error">Locked</span>`;
      } else if (a.must_change_password) {
        stateChip = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#8a6100]/10 text-[#8a6100]">Temp password</span>`;
      } else if (String(a.status).toUpperCase() !== "ACTIVE") {
        stateChip = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-error/10 text-error">Disabled</span>`;
      }

      const tr = document.createElement("tr");
      tr.className = "hover:bg-surface-container-low transition-colors cursor-pointer";
      tr.onclick = () => { document.getElementById("support-identifier").value = a.mobile_number || a.user_id; };
      tr.innerHTML = `
        <td class="p-3 font-bold text-on-surface">${escapeHtml(a.name)}</td>
        <td class="p-3 text-on-surface-variant">${escapeHtml(a.mobile_number || "—")}</td>
        <td class="p-3 text-on-surface-variant">${escapeHtml(a.functionary_type || a.role)}</td>
        <td class="p-3 text-on-surface-variant text-[11px]">${escapeHtml((a.created_at || "").slice(0, 16))}</td>
        <td class="p-3 text-on-surface-variant text-[11px]">${escapeHtml((a.last_login_at || "Never").slice(0, 16))}</td>
        <td class="p-3">${stateChip}${a.failed_attempts ? `<span class="ml-1 text-[10px] text-on-surface-variant">${a.failed_attempts} failed</span>` : ""}</td>`;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-error">Could not load accounts.</td></tr>`;
  }
}

async function loadAuthAudit() {
  const box = document.getElementById("admin-auth-audit");
  if (!box) return;
  try {
    const res = await apiFetch("/api/admin/auth-audit?limit=40");
    const data = await res.json();
    if (!data.success || !data.events.length) {
      box.innerHTML = `<p class="text-xs text-on-surface-variant p-2 text-center">No sign-in activity recorded yet.</p>`;
      return;
    }
    const toneFor = outcome =>
      outcome === "success" ? "text-[#2e7d32]" : outcome === "locked" ? "text-error" : "text-[#8a6100]";

    box.innerHTML = data.events.map(e => `
      <div class="flex items-center gap-2 text-[11px] p-2 rounded-lg border border-outline-variant/30 bg-surface">
        <span class="font-semibold ${toneFor(e.outcome)} shrink-0">${escapeHtml(e.outcome || "")}</span>
        <span class="font-medium text-on-surface shrink-0">${escapeHtml(e.event)}</span>
        <span class="text-on-surface-variant truncate">${escapeHtml(e.account || "")}${e.detail ? " • " + escapeHtml(e.detail) : ""}</span>
        <span class="ml-auto text-on-surface-variant shrink-0">${escapeHtml((e.created_at || "").slice(0, 16))}</span>
      </div>`).join("");
  } catch (err) {
    box.innerHTML = `<p class="text-xs text-error p-2">Could not load sign-in activity.</p>`;
  }
}

// ==================== 9b. FIELD ATTENDANCE (USER SIDE) ====================
/**
 * Daily attendance marking.
 *
 * The mobile number entered in the form is the identity key: the backend
 * enforces one row per (mobile number, IST date), so submitting again on the
 * same day always UPDATES that entry instead of creating a duplicate. Name,
 * position and block number carry forward from the person's last submission,
 * so a returning user only re-takes the photo and re-confirms their location.
 */

const ATTENDANCE_STATUS_STYLES = {
  PENDING:  { chip: "bg-[#8a6100]/10 text-[#8a6100]", label: "Pending review",
              banner: "bg-[#8a6100]/10 border-[#8a6100]/30", icon: "hourglass_top", iconClass: "text-[#8a6100]" },
  APPROVED: { chip: "bg-[#2e7d32]/10 text-[#2e7d32]", label: "Approved",
              banner: "bg-[#2e7d32]/10 border-[#2e7d32]/30", icon: "verified", iconClass: "text-[#2e7d32]" },
  REJECTED: { chip: "bg-error/10 text-error", label: "Rejected",
              banner: "bg-error/10 border-error/30", icon: "error", iconClass: "text-error" }
};

function todayIstString() {
  // The register's day boundary is IST (matching the backend), so derive it
  // from UTC rather than trusting whatever timezone the device is set to.
  const now = new Date();
  const istMs = now.getTime() + now.getTimezoneOffset() * 60000 + 5.5 * 3600000;
  return new Date(istMs).toISOString().slice(0, 10);
}

function formatDateLong(isoDate) {
  if (!isoDate) return "";
  const [y, m, d] = isoDate.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  return dt.toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
}

/**
 * Reflect today's attendance state on the home page card, so a user can see
 * at a glance whether they still need to mark attendance.
 */
function updateHomeAttendanceChip(record) {
  const chip = document.getElementById("home-attendance-chip");
  const subtitle = document.getElementById("home-attendance-subtitle");
  if (!chip || !subtitle) return;

  if (!record) {
    chip.classList.add("hidden");
    subtitle.textContent = I18N[state.currentLanguage] && I18N[state.currentLanguage].attendance_home_sub
      ? I18N[state.currentLanguage].attendance_home_sub
      : "Submit your name, position, block number, photo and live location.";
    return;
  }

  const style = ATTENDANCE_STATUS_STYLES[record.status] || ATTENDANCE_STATUS_STYLES.PENDING;
  chip.className = `shrink-0 px-2.5 py-1 rounded-full text-[10px] font-bold ${style.chip}`;
  chip.textContent = style.label;
  chip.classList.remove("hidden");
  subtitle.textContent = record.status === "APPROVED"
    ? "Today's attendance is approved and final."
    : record.status === "REJECTED"
      ? "Sent back for correction — tap to fix and resubmit."
      : "Marked for today. Tap to review or edit your entry.";
}

/**
 * Called once the app shell is shown, so the home card already knows today's
 * status without the user opening the Attendance tab first.
 */
async function refreshHomeAttendanceStatus() {
  const raw = state.currentUser && state.currentUser.mobile_number;
  const digits = String(raw || "").replace(/\D/g, "").slice(-10);
  if (digits.length !== 10) return;
  try {
    const res = await apiFetch(`/api/attendance/lookup?mobile=${digits}`);
    const data = await res.json();
    if (data.success) updateHomeAttendanceChip(data.record);
  } catch (err) {
    /* the card simply stays in its default state */
  }
}

function initAttendanceView() {
  const todayLabel = document.getElementById("attendance-today-label");
  if (todayLabel) todayLabel.textContent = formatDateLong(todayIstString());

  const mobileInput = document.getElementById("att-mobile");
  if (!mobileInput) return;

  // Prefill from the signed-in functionary's own verified mobile number.
  if (!mobileInput.value && state.currentUser && state.currentUser.mobile_number) {
    const digits = String(state.currentUser.mobile_number).replace(/\D/g, "").slice(-10);
    if (digits.length === 10) mobileInput.value = digits;
  }
  if (!mobileInput.value && state.currentUser && state.currentUser.name && !document.getElementById("att-name").value) {
    document.getElementById("att-name").value = state.currentUser.name;
  }

  if (mobileInput.value.length === 10) {
    lookupAttendance(mobileInput.value);
  }
  if (!state.attendance.location) {
    captureAttendanceLocation({ silent: true });
  }
}

function handleAttendanceMobileInput() {
  const input = document.getElementById("att-mobile");
  input.value = input.value.replace(/\D/g, "").slice(0, 10);

  clearTimeout(state.attendance.lookupTimer);
  if (input.value.length !== 10) {
    state.attendance.record = null;
    renderAttendanceState();
    return;
  }
  state.attendance.lookupTimer = setTimeout(() => lookupAttendance(input.value), 250);
}

async function lookupAttendance(mobile) {
  try {
    const res = await apiFetch(`/api/attendance/lookup?mobile=${encodeURIComponent(mobile)}`);
    const data = await res.json();
    if (!data.success) return;

    state.attendance.record = data.record || null;
    state.attendance.editing = false;

    // Carry forward name / position / block: today's record wins, otherwise
    // the most recent previous submission.
    const source = data.record || data.profile;
    if (source) {
      const nameEl = document.getElementById("att-name");
      const blockEl = document.getElementById("att-block");
      if (nameEl && !nameEl.value) nameEl.value = source.name || "";
      if (blockEl && !blockEl.value) blockEl.value = source.block_number || "";
      const posRadio = document.querySelector(`input[name="att-position"][value="${source.position}"]`);
      if (posRadio && !document.querySelector('input[name="att-position"]:checked')) {
        posRadio.checked = true;
        handleAttendancePositionChange();
      }
      if (!data.record && data.profile) {
        showToast(`Details carried forward from ${formatDateLong(data.profile.from_date)}.`);
      }
    }
    renderAttendanceState();
  } catch (err) {
    // A failed lookup must never block a fresh submission.
    console.warn("Attendance lookup failed", err);
  }
}

function handleAttendancePositionChange() {
  const picked = document.querySelector('input[name="att-position"]:checked');
  const label = document.getElementById("att-block-label");
  const hint = document.getElementById("att-block-hint");
  const input = document.getElementById("att-block");
  if (!picked || !label) return;

  if (picked.value === "Supervisor") {
    label.innerHTML = `Supervisory Circle Number <span class="text-error">*</span>`;
    if (input) input.placeholder = "e.g. 07";
    if (hint) hint.textContent = "The Supervisory Circle number assigned to you.";
  } else {
    label.innerHTML = `HLB Number <span class="text-error">*</span>`;
    if (input) input.placeholder = "e.g. 0142";
    if (hint) hint.textContent = "The House Listing Block number assigned to you.";
  }
}

/**
 * Downscale a camera photo before upload. Field staff are on mobile data and
 * a raw 12-megapixel capture is 4-6 MB; 1280px JPEG is 200-400 KB and still
 * perfectly clear for identity verification.
 */
async function downscaleImage(file, maxDim = 1280, quality = 0.82) {
  const bitmap = await (window.createImageBitmap
    ? createImageBitmap(file, { imageOrientation: "from-image" }).catch(() => createImageBitmap(file))
    : new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = URL.createObjectURL(file);
      }));

  const w = bitmap.width || bitmap.naturalWidth;
  const h = bitmap.height || bitmap.naturalHeight;
  const scale = Math.min(1, maxDim / Math.max(w, h));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(w * scale);
  canvas.height = Math.round(h * scale);
  canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  if (bitmap.close) bitmap.close();

  return new Promise(resolve => canvas.toBlob(b => resolve(b || file), "image/jpeg", quality));
}

async function handleAttendancePhotoPick(input) {
  const file = input.files && input.files[0];
  if (!file) return;

  if (!file.type.startsWith("image/")) {
    showToast("Please choose an image file.");
    input.value = "";
    return;
  }

  try {
    const blob = await downscaleImage(file);
    state.attendance.photoBlob = blob;
    state.attendance.photoName = "attendance.jpg";

    const preview = document.getElementById("att-photo-preview");
    if (preview.dataset.objectUrl) URL.revokeObjectURL(preview.dataset.objectUrl);
    const url = URL.createObjectURL(blob);
    preview.dataset.objectUrl = url;
    preview.src = url;

    document.getElementById("att-photo-empty").classList.add("hidden");
    document.getElementById("att-photo-preview-wrap").classList.remove("hidden");
    document.getElementById("att-photo-caption").textContent = "New photo ready to submit";
    document.getElementById("att-photo-size").textContent = `${Math.round(blob.size / 1024)} KB`;
  } catch (err) {
    showToast("Could not read that photo. Please try again.");
  } finally {
    input.value = "";  // let the same file be re-picked
  }
}

function captureAttendanceLocation(options = {}) {
  const { silent = false } = options;
  const icon = document.getElementById("att-location-icon");
  const title = document.getElementById("att-location-title");
  const detail = document.getElementById("att-location-detail");
  const btn = document.getElementById("att-location-btn");
  const mapLink = document.getElementById("att-location-map-link");
  if (!title) return;

  if (!navigator.geolocation) {
    title.textContent = "Location not supported";
    detail.textContent = "This device or browser cannot provide GPS coordinates.";
    return;
  }
  if (!window.isSecureContext && location.protocol !== "file:") {
    title.textContent = "Location blocked (insecure connection)";
    detail.textContent = "Open the app over HTTPS — browsers only give GPS access on a secure connection.";
    if (icon) { icon.textContent = "location_off"; icon.className = "material-symbols-outlined text-error"; }
    return;
  }

  if (btn) { btn.disabled = true; btn.textContent = "Locating..."; }
  title.textContent = "Reading your location...";
  detail.textContent = "Keep the app open and stay outdoors if possible.";
  if (icon) { icon.textContent = "my_location"; icon.className = "material-symbols-outlined text-primary animate-pulse"; }

  navigator.geolocation.getCurrentPosition(
    pos => {
      const { latitude, longitude, accuracy } = pos.coords;
      state.attendance.location = { latitude, longitude, accuracy };

      title.textContent = "Location captured";
      detail.textContent = `${latitude.toFixed(6)}, ${longitude.toFixed(6)} • accurate to ~${Math.round(accuracy)} m`;
      if (icon) { icon.textContent = "location_on"; icon.className = "material-symbols-outlined text-[#2e7d32]"; }
      if (btn) { btn.disabled = false; btn.textContent = "Recapture"; }
      if (mapLink) {
        mapLink.href = `https://www.google.com/maps?q=${latitude},${longitude}`;
        mapLink.classList.remove("hidden");
      }
    },
    err => {
      const messages = {
        1: "Location permission denied. Allow location access for this app and tap Capture again.",
        2: "Your location is unavailable right now. Move to an open area and retry.",
        3: "Location request timed out. Please tap Capture again."
      };
      title.textContent = "Location not captured";
      detail.textContent = messages[err.code] || "Could not read your location.";
      if (icon) { icon.textContent = "location_off"; icon.className = "material-symbols-outlined text-error"; }
      if (btn) { btn.disabled = false; btn.textContent = "Capture"; }
      if (!silent) showToast(detail.textContent);
    },
    { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
  );
}

async function handleAttendanceSubmit(event) {
  event.preventDefault();

  const mobile = (document.getElementById("att-mobile").value || "").replace(/\D/g, "");
  const name = (document.getElementById("att-name").value || "").trim();
  const position = (document.querySelector('input[name="att-position"]:checked') || {}).value;
  const block = (document.getElementById("att-block").value || "").trim();

  if (mobile.length !== 10) return showToast("Enter a valid 10-digit mobile number.");
  if (name.length < 2) return showToast("Enter your full name.");
  if (!position) return showToast("Select whether you are an Enumerator or a Supervisor.");
  if (!block) return showToast("Enter your HLB / Supervisory Circle number.");
  if (!state.attendance.location) return showToast("Capture your current location before submitting.");

  const existing = state.attendance.record;
  if (!existing && !state.attendance.photoBlob) {
    return showToast("Take a photo before submitting.");
  }

  const form = new FormData();
  form.append("mobile_number", mobile);
  form.append("name", name);
  form.append("position", position);
  form.append("block_number", block);
  form.append("latitude", state.attendance.location.latitude);
  form.append("longitude", state.attendance.location.longitude);
  if (state.attendance.location.accuracy != null) {
    form.append("accuracy_m", state.attendance.location.accuracy);
  }
  if (state.attendance.photoBlob) {
    form.append("photo", state.attendance.photoBlob, state.attendance.photoName || "attendance.jpg");
  }

  const btn = document.getElementById("att-submit-btn");
  const label = document.getElementById("att-submit-label");
  const originalLabel = label.textContent;
  btn.disabled = true;
  label.textContent = "Submitting...";

  try {
    const res = await apiFetch("/api/attendance/submit", { method: "POST", body: form });
    const data = await res.json();

    if (!data.success) {
      showToast(data.error || "Could not submit attendance.");
      if (data.locked && data.record) {
        state.attendance.record = data.record;
        state.attendance.editing = false;
        renderAttendanceState();
      }
      return;
    }

    state.attendance.record = data.record;
    state.attendance.editing = false;
    state.attendance.photoBlob = null;
    clearAttendancePhotoPreview();
    renderAttendanceState();
    showToast(data.created ? "Attendance submitted." : "Attendance updated — still one entry for today.");
  } catch (err) {
    showToast("Network error. Check your connection and try again.");
  } finally {
    btn.disabled = false;
    label.textContent = originalLabel;
  }
}

function clearAttendancePhotoPreview() {
  const preview = document.getElementById("att-photo-preview");
  if (preview && preview.dataset.objectUrl) {
    URL.revokeObjectURL(preview.dataset.objectUrl);
    delete preview.dataset.objectUrl;
    preview.removeAttribute("src");
  }
  const emptyEl = document.getElementById("att-photo-empty");
  const wrapEl = document.getElementById("att-photo-preview-wrap");
  if (emptyEl) emptyEl.classList.remove("hidden");
  if (wrapEl) wrapEl.classList.add("hidden");
}

function resetAttendanceForm() {
  document.getElementById("att-name").value = "";
  document.getElementById("att-block").value = "";
  document.querySelectorAll('input[name="att-position"]').forEach(r => { r.checked = false; });
  state.attendance.photoBlob = null;
  clearAttendancePhotoPreview();
  showToast("Form cleared. Your submitted entry is unchanged.");
}

function enableAttendanceEdit() {
  state.attendance.editing = true;
  renderAttendanceState();
  document.getElementById("attendance-form").scrollIntoView({ behavior: "smooth", block: "start" });
}

/**
 * Single place that decides what the Attendance tab shows: the form, the
 * read-only summary of an already-submitted entry, and the status banner.
 */
function renderAttendanceState() {
  const record = state.attendance.record;
  const banner = document.getElementById("attendance-status-banner");
  const summary = document.getElementById("attendance-summary");
  const form = document.getElementById("attendance-form");
  const submitLabel = document.getElementById("att-submit-label");
  const editBtn = document.getElementById("att-edit-btn");
  if (!banner || !summary || !form) return;

  updateHomeAttendanceChip(record);

  if (!record) {
    banner.classList.add("hidden");
    summary.classList.add("hidden");
    form.classList.remove("hidden");
    if (submitLabel) submitLabel.textContent = "Submit Attendance";
    return;
  }

  const style = ATTENDANCE_STATUS_STYLES[record.status] || ATTENDANCE_STATUS_STYLES.PENDING;
  const locked = record.status === "APPROVED";

  // ---- Banner ----
  let bannerBody = "";
  if (record.status === "APPROVED") {
    bannerBody = `Your attendance for ${escapeHtml(formatDateLong(record.attendance_date))} has been approved by the
      Technical Assistant and is now final. Your photo has been deleted from the server.`;
  } else if (record.status === "REJECTED") {
    bannerBody = `Your entry was sent back for correction.<br><strong>Reason:</strong>
      ${escapeHtml(record.reject_reason || "Not specified")}<br>Correct the details below and resubmit.`;
  } else {
    bannerBody = `Your attendance for ${escapeHtml(formatDateLong(record.attendance_date))} is recorded and waiting for
      the Technical Assistant to review it. You can still edit and resubmit until then.`;
  }
  banner.className = `rounded-2xl p-4 border flex items-start gap-3 ${style.banner}`;
  banner.innerHTML = `
    <span class="material-symbols-outlined ${style.iconClass} mt-0.5">${style.icon}</span>
    <div class="text-sm text-on-surface leading-relaxed">
      <p class="font-bold mb-0.5">${escapeHtml(style.label)}</p>
      <p class="text-on-surface-variant">${bannerBody}</p>
    </div>`;
  banner.classList.remove("hidden");

  // ---- Summary ----
  document.getElementById("att-summary-date").textContent = formatDateLong(record.attendance_date);
  document.getElementById("att-summary-meta").textContent =
    `Submitted ${record.submitted_at || "—"}${record.submission_count > 1 ? ` • edited ${record.submission_count - 1} time(s)` : ""}`;

  const statusChip = document.getElementById("att-summary-status");
  statusChip.className = `shrink-0 px-2.5 py-1 rounded-full text-[10px] font-bold ${style.chip}`;
  statusChip.textContent = style.label;

  const blockLabel = record.position === "Supervisor" ? "Supervisory Circle" : "HLB Number";
  document.getElementById("att-summary-fields").innerHTML = `
    <div><dt class="text-xs text-on-surface-variant">Name</dt><dd class="font-semibold text-on-surface">${escapeHtml(record.name)}</dd></div>
    <div><dt class="text-xs text-on-surface-variant">Position</dt><dd class="font-semibold text-on-surface">${escapeHtml(record.position)}</dd></div>
    <div><dt class="text-xs text-on-surface-variant">${blockLabel}</dt><dd class="font-semibold text-on-surface">${escapeHtml(record.block_number)}</dd></div>
    <div><dt class="text-xs text-on-surface-variant">Mobile</dt><dd class="font-semibold text-on-surface">+91 ${escapeHtml(record.mobile_number)}</dd></div>
    <div class="sm:col-span-2"><dt class="text-xs text-on-surface-variant">Location</dt>
      <dd class="font-semibold text-on-surface">
        ${Number(record.latitude).toFixed(6)}, ${Number(record.longitude).toFixed(6)}
        <a href="${escapeAttr(record.maps_link)}" target="_blank" rel="noopener noreferrer"
           class="ml-1 text-primary font-semibold hover:underline">View on map</a>
      </dd></div>`;
  summary.classList.remove("hidden");
  if (editBtn) editBtn.classList.toggle("hidden", locked);

  // ---- Form visibility ----
  const showForm = !locked && (state.attendance.editing || record.status === "REJECTED");
  form.classList.toggle("hidden", !showForm);
  if (submitLabel) submitLabel.textContent = "Update Attendance";

  if (showForm) {
    document.getElementById("att-mobile").value = record.mobile_number;
    document.getElementById("att-name").value = record.name;
    document.getElementById("att-block").value = record.block_number;
    const posRadio = document.querySelector(`input[name="att-position"][value="${record.position}"]`);
    if (posRadio) posRadio.checked = true;
    handleAttendancePositionChange();
    const caption = document.getElementById("att-photo-caption");
    if (caption && !state.attendance.photoBlob && record.has_photo) {
      document.getElementById("att-photo-empty").classList.remove("hidden");
      caption.textContent = "Photo already on file";
    }
  }
}

// ==================== 9c. FIELD ATTENDANCE (ADMIN SIDE) ====================

function setAttendanceStatusFilter(status) {
  state.adminAttendance.status = status;
  loadAdminAttendance();
}

function debounceAdminAttendanceSearch() {
  clearTimeout(state.adminAttendance.searchTimer);
  state.adminAttendance.searchTimer = setTimeout(loadAdminAttendance, 300);
}

function currentAttendanceFilters() {
  const val = id => (document.getElementById(id) || {}).value || "";
  return {
    status: state.adminAttendance.status,
    position: val("att-filter-position"),
    date_from: val("att-filter-from"),
    date_to: val("att-filter-to"),
    q: val("att-filter-q").trim()
  };
}

function attendanceFilterQuery() {
  const f = currentAttendanceFilters();
  return Object.entries(f)
    .filter(([, v]) => v)
    .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
    .join("&");
}

async function loadAdminAttendance() {
  const tbody = document.getElementById("admin-attendance-table-body");
  if (!tbody) return;

  // Reflect the active status chip
  [["", "all"], ["PENDING", "pending"], ["APPROVED", "approved"], ["REJECTED", "rejected"]].forEach(([value, key]) => {
    const chip = document.getElementById(`att-chip-${key}`);
    if (!chip) return;
    const active = state.adminAttendance.status === value;
    chip.classList.toggle("bg-primary", active);
    chip.classList.toggle("text-white", active);
    chip.classList.toggle("border-primary", active);
    chip.classList.toggle("text-on-surface-variant", !active);
  });

  try {
    const res = await apiFetch(`/api/admin/attendance?${attendanceFilterQuery()}&limit=200`);
    const data = await res.json();

    if (!data.success) {
      tbody.innerHTML = `<tr><td colspan="9" class="p-4 text-center text-error">${escapeHtml(data.error || "Could not load the register.")}</td></tr>`;
      return;
    }

    const s = data.summary || {};
    const setCount = (id, n) => { const el = document.getElementById(id); if (el) el.textContent = n || 0; };
    setCount("att-count-all", s.all);
    setCount("att-count-pending", s.pending);
    setCount("att-count-approved", s.approved);
    setCount("att-count-rejected", s.rejected);

    tbody.innerHTML = "";
    if (!data.records.length) {
      tbody.innerHTML = `<tr><td colspan="9" class="p-4 text-center text-on-surface-variant">No attendance entries match these filters.</td></tr>`;
      document.getElementById("admin-attendance-footer").textContent = "";
      return;
    }

    data.records.forEach(rec => {
      const style = ATTENDANCE_STATUS_STYLES[rec.status] || ATTENDANCE_STATUS_STYLES.PENDING;

      let photoCell;
      if (rec.has_photo) {
        photoCell = `<button onclick="openAttendancePhoto(${rec.id}, '${escapeAttr(rec.name)}', '${escapeAttr(rec.attendance_date)}')"
            class="text-primary font-semibold hover:underline flex items-center gap-1">
            <span class="material-symbols-outlined text-base">image</span> View</button>`;
      } else if (rec.photo_deleted) {
        photoCell = `<span class="text-on-surface-variant flex items-center gap-1" title="Deleted automatically on approval">
            <span class="material-symbols-outlined text-base">delete_forever</span> Deleted</span>`;
      } else {
        photoCell = `<span class="text-on-surface-variant">—</span>`;
      }

      const reviewCell = rec.status === "PENDING"
        ? `<div class="flex items-center justify-end gap-1.5">
             <button onclick="approveAttendance(${rec.id})"
               class="text-[11px] font-semibold px-2.5 py-1 rounded border border-[#2e7d32]/40 text-[#2e7d32] hover:bg-[#2e7d32]/10 transition-all">Approve</button>
             <button onclick="openAttendanceRejectModal(${rec.id}, '${escapeAttr(rec.name)} — ${escapeAttr(rec.attendance_date)}')"
               class="text-[11px] font-semibold px-2.5 py-1 rounded border border-error/40 text-error hover:bg-error-container/30 transition-all">Reject</button>
           </div>`
        : `<div class="flex items-center justify-end gap-1.5">
             <span class="text-[10px] text-on-surface-variant">${escapeHtml(rec.reviewed_by || "")}</span>
             <button onclick="deleteAttendanceRecord(${rec.id}, '${escapeAttr(rec.name)}')" title="Delete this entry"
               class="text-on-surface-variant hover:text-error p-1 rounded transition-colors">
               <span class="material-symbols-outlined text-base">delete</span></button>
           </div>`;

      const tr = document.createElement("tr");
      tr.className = "hover:bg-surface-container-low transition-colors align-top";
      tr.innerHTML = `
        <td class="p-3 font-mono text-[11px] text-on-surface-variant whitespace-nowrap">${escapeHtml(rec.attendance_date)}</td>
        <td class="p-3 font-bold text-on-surface">${escapeHtml(rec.name)}
          ${rec.submission_count > 1 ? `<span class="ml-1 text-[10px] font-normal text-on-surface-variant">(edited ${rec.submission_count - 1}×)</span>` : ""}
          ${rec.reject_reason ? `<div class="text-[10px] text-error font-normal mt-0.5">${escapeHtml(rec.reject_reason)}</div>` : ""}
        </td>
        <td class="p-3 text-on-surface-variant whitespace-nowrap">${escapeHtml(rec.mobile_number)}</td>
        <td class="p-3 text-on-surface-variant">${escapeHtml(rec.position)}</td>
        <td class="p-3 font-mono text-on-surface">${escapeHtml(rec.block_number)}</td>
        <td class="p-3">
          <a href="${escapeAttr(rec.maps_link)}" target="_blank" rel="noopener noreferrer"
             class="text-primary font-semibold hover:underline whitespace-nowrap">
            ${Number(rec.latitude).toFixed(4)}, ${Number(rec.longitude).toFixed(4)}</a>
          ${rec.accuracy_m ? `<div class="text-[10px] text-on-surface-variant">±${Math.round(rec.accuracy_m)} m</div>` : ""}
        </td>
        <td class="p-3">${photoCell}</td>
        <td class="p-3"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${style.chip}">${escapeHtml(style.label)}</span></td>
        <td class="p-3 text-right">${reviewCell}</td>`;
      tbody.appendChild(tr);
    });

    document.getElementById("admin-attendance-footer").textContent =
      `Showing ${data.records.length} of ${data.total} matching entries.`;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="9" class="p-4 text-center text-error">Error loading the attendance register.</td></tr>`;
  }
}

/**
 * Photos are admin-gated, so they cannot be loaded with a plain <img src>
 * (no Authorization header). Fetch the bytes with the bearer token and hand
 * the <img> an object URL instead.
 */
async function openAttendancePhoto(recordId, name, date) {
  const modal = document.getElementById("modal-attendance-photo");
  const img = document.getElementById("att-photo-modal-img");
  document.getElementById("att-photo-modal-title").textContent = name || "Attendance photo";
  document.getElementById("att-photo-modal-sub").textContent = date ? formatDateLong(date) : "";
  img.removeAttribute("src");
  modal.classList.remove("hidden");

  try {
    const res = await apiFetch(`/api/admin/attendance/${recordId}/photo`);
    if (!res.ok) {
      showToast("This photo is no longer on the server.");
      closeAttendancePhotoModal();
      return;
    }
    const blob = await res.blob();
    if (state.adminAttendance.photoObjectUrl) URL.revokeObjectURL(state.adminAttendance.photoObjectUrl);
    state.adminAttendance.photoObjectUrl = URL.createObjectURL(blob);
    img.src = state.adminAttendance.photoObjectUrl;
  } catch (err) {
    showToast("Could not load the photo.");
    closeAttendancePhotoModal();
  }
}

function closeAttendancePhotoModal() {
  document.getElementById("modal-attendance-photo").classList.add("hidden");
  if (state.adminAttendance.photoObjectUrl) {
    URL.revokeObjectURL(state.adminAttendance.photoObjectUrl);
    state.adminAttendance.photoObjectUrl = null;
  }
}

async function approveAttendance(recordId) {
  try {
    const res = await apiFetch(`/api/admin/attendance/${recordId}/approve`, { method: "POST" });
    const data = await res.json();
    showToast(data.success ? data.message : (data.error || "Could not approve this entry."));
    if (data.success) loadAdminAttendance();
  } catch (err) {
    showToast("Network error while approving.");
  }
}

function openAttendanceRejectModal(recordId, label) {
  state.adminAttendance.rejectTargetId = recordId;
  document.getElementById("att-reject-target").textContent = label || "";
  document.getElementById("att-reject-reason").value = "";
  document.getElementById("modal-attendance-reject").classList.remove("hidden");
}

function closeAttendanceRejectModal() {
  state.adminAttendance.rejectTargetId = null;
  document.getElementById("modal-attendance-reject").classList.add("hidden");
}

async function confirmAttendanceReject() {
  const recordId = state.adminAttendance.rejectTargetId;
  const reason = (document.getElementById("att-reject-reason").value || "").trim();
  if (!recordId) return;
  if (!reason) return showToast("Give a reason so the user knows what to correct.");

  try {
    const res = await apiFetch(`/api/admin/attendance/${recordId}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason })
    });
    const data = await res.json();
    showToast(data.success ? data.message : (data.error || "Could not reject this entry."));
    if (data.success) {
      closeAttendanceRejectModal();
      loadAdminAttendance();
    }
  } catch (err) {
    showToast("Network error while rejecting.");
  }
}

async function deleteAttendanceRecord(recordId, name) {
  if (!confirm(`Permanently delete the attendance entry for ${name}? This cannot be undone.`)) return;
  try {
    const res = await apiFetch(`/api/admin/attendance/${recordId}`, { method: "DELETE" });
    const data = await res.json();
    showToast(data.success ? data.message : (data.error || "Could not delete the entry."));
    if (data.success) loadAdminAttendance();
  } catch (err) {
    showToast("Network error while deleting.");
  }
}

/**
 * Export the filtered register as ONE Excel workbook containing every user's
 * entries. Fetched as a blob because the endpoint is bearer-token gated.
 */
async function exportAttendanceExcel(btn) {
  const original = btn ? btn.innerHTML : "";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="material-symbols-outlined text-base animate-spin">progress_activity</span><span>Building...</span>`;
  }

  try {
    const res = await apiFetch(`/api/admin/attendance/export?${attendanceFilterQuery()}`);
    if (!res.ok) {
      showToast("Could not build the Excel file.");
      return;
    }
    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : `Census_Attendance_${todayIstString()}.xlsx`;

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    showToast(`Downloaded ${filename}`);
  } catch (err) {
    showToast("Network error while exporting.");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = original;
    }
  }
}

// ==================== 10. LANGUAGE & UTILITY FUNCTIONS ====================
function changeLanguage(langCode) {
  if (!I18N[langCode]) langCode = "en";
  state.currentLanguage = langCode;
  localStorage.setItem("census_lang", langCode);
  applyLanguage(langCode);

  ["en", "as", "hi", "bn"].forEach(l => {
    const btn = document.getElementById(`lang-btn-${l}`);
    if (btn) {
      if (l === langCode) {
        btn.className = "flex flex-col items-center justify-center p-3.5 rounded-xl border-2 border-primary bg-primary-fixed/30 text-primary transition-all";
      } else {
        btn.className = "flex flex-col items-center justify-center p-3.5 rounded-xl border border-outline-variant bg-surface-container-lowest text-on-surface hover:bg-surface-container-low transition-all";
      }
    }
  });

  const headerSelect = document.getElementById("header-lang-select");
  if (headerSelect) headerSelect.value = langCode;
}

function applyLanguage(lang) {
  const dict = I18N[lang] || I18N.en;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.textContent = dict[key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (dict[key]) el.placeholder = dict[key];
  });
}

function toggleDarkMode(isDark) {
  if (isDark) {
    document.documentElement.classList.add("dark");
    localStorage.setItem("census_dark", "true");
  } else {
    document.documentElement.classList.remove("dark");
    localStorage.setItem("census_dark", "false");
  }
}

function toggleMobileDrawer() {
  const drawer = document.getElementById("mobile-drawer");
  const backdrop = document.getElementById("mobile-drawer-backdrop");
  if (!drawer || !backdrop) return;
  const isOpen = !drawer.classList.contains("hidden");
  if (isOpen) {
    drawer.classList.add("-translate-x-full");
    setTimeout(() => {
      drawer.classList.add("hidden");
      backdrop.classList.add("hidden");
    }, 200);
  } else {
    drawer.classList.remove("hidden");
    backdrop.classList.remove("hidden");
    // Force reflow so the transition plays
    void drawer.offsetWidth;
    drawer.classList.remove("-translate-x-full");
  }
}

function navigateFromDrawer(view) {
  toggleMobileDrawer();
  navigateTo(view);
}

function triggerVoiceInput(targetInputId) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showToast("Voice input is not supported in this browser.");
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = state.currentLanguage === "as" ? "as-IN" : (state.currentLanguage === "hi" ? "hi-IN" : (state.currentLanguage === "bn" ? "bn-IN" : "en-IN"));
  recognition.interimResults = false;

  showToast("Listening... Speak now.");
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    const input = document.getElementById(targetInputId);
    if (input) {
      input.value = transcript;
      if (targetInputId === "chat-input") {
        handleSendChat({ preventDefault: () => {} });
      }
    }
  };
  recognition.onerror = () => {
    showToast("Voice recognition error or cancelled.");
  };
  recognition.start();
}

function showToast(msg) {
  const toast = document.getElementById("toast-notification");
  const msgEl = document.getElementById("toast-message");
  if (toast && msgEl) {
    msgEl.textContent = msg;
    toast.classList.remove("hidden");
    setTimeout(() => {
      toast.classList.add("hidden");
    }, 3500);
  }
}

function copyToClipboard(btn) {
  const parent = btn.closest(".flex-col");
  const textEl = parent ? parent.querySelector(".bg-surface-container-lowest") : null;
  if (textEl) {
    navigator.clipboard.writeText(textEl.innerText);
    showToast("Copied to clipboard!");
  }
}

function shareText(text) {
  nativeShare("Census Assistant", text);
}

function openPrivacyModal() {
  alert("Official Privacy Policy:\n\nAll census data collection, enumerator records, and supervisory allocations are strictly confidential and governed under the Census Act, 1948. Unauthorized dissemination is strictly prohibited.");
}

function formatMarkdown(text) {
  // AI answers embed the raw Google Maps URL inline (e.g. "• **Google Maps:**
  // https://www.google.com/maps/..."), which used to render as a long,
  // unclickable wall of text once escaped. Pull those URLs out into
  // placeholders BEFORE escaping so we can swap in a proper map button
  // afterwards, instead of ever exposing the long link itself.
  const mapsUrls = [];
  let working = String(text || "").replace(
    /https?:\/\/(?:www\.)?google\.com\/maps\/search\/\?api=1&query=[^\s<>()\[\]]+/g,
    (match) => {
      mapsUrls.push(match);
      return `%%MAPS_LINK_${mapsUrls.length - 1}%%`;
    }
  );

  let html = escapeHtml(working);
  // Bold **text**
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic *text*
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Code `text`
  html = html.replace(/`(.*?)`/g, '<code class="bg-surface-container px-1 py-0.5 rounded text-primary text-xs font-mono">$1</code>');
  // Bullet lists
  html = html.replace(/^• (.*?)$/gm, '<li class="ml-4 list-disc">$1</li>');
  // Newlines
  html = html.replace(/\n/g, '<br/>');

  // Swap the placeholders back in as map buttons rather than raw links.
  html = html.replace(/%%MAPS_LINK_(\d+)%%/g, (_, idx) => {
    const url = mapsUrls[Number(idx)];
    if (!url) return "";
    return `<a href="${escapeAttr(url)}" target="_blank" rel="noopener noreferrer"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 text-primary hover:bg-primary hover:text-white transition-colors text-xs font-semibold align-middle">
        <span class="material-symbols-outlined text-[15px]">map</span>
        <span>Open in Google Maps</span>
      </a>`;
  });

  return html;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr(str) {
  if (!str) return "";
  return String(str).replace(/'/g, "\\'").replace(/\n/g, " ");
}
