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
    nav_alerts: "Alerts",
    nav_settings: "Settings",
    nav_admin: "Admin",
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
    nav_alerts: "বিজ্ঞপ্তি",
    nav_settings: "ছেটিংছ",
    nav_admin: "এডমিন",
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
    nav_alerts: "सूचनाएं",
    nav_settings: "सेटिंग्स",
    nav_admin: "व्यवस्थापक",
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
    nav_alerts: "বিজ্ঞপ্তি",
    nav_settings: "সেটিংস",
    nav_admin: "অ্যাডমিন",
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
  searchDebounceTimer: null
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
  const validViews = ["home", "search", "chat", "manual", "supervisor", "notifications", "settings", "admin"];
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
  } else if (viewName === "notifications") {
    loadNotifications();
  } else if (viewName === "supervisor") {
    loadSupervisors();
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
function switchLoginTab(tab) {
  const formOtp = document.getElementById("form-otp");
  const formAdmin = document.getElementById("form-admin");
  const btnOtp = document.getElementById("tab-btn-otp");
  const btnAdmin = document.getElementById("tab-btn-admin");

  if (tab === "otp") {
    formOtp.classList.remove("hidden");
    formAdmin.classList.add("hidden");
    btnOtp.classList.add("border-primary", "text-primary");
    btnOtp.classList.remove("border-transparent", "text-on-surface-variant");
    btnAdmin.classList.remove("border-primary", "text-primary");
    btnAdmin.classList.add("border-transparent", "text-on-surface-variant");
  } else {
    formOtp.classList.add("hidden");
    formAdmin.classList.remove("hidden");
    btnAdmin.classList.add("border-primary", "text-primary");
    btnAdmin.classList.remove("border-transparent", "text-on-surface-variant");
    btnOtp.classList.remove("border-primary", "text-primary");
    btnOtp.classList.add("border-transparent", "text-on-surface-variant");
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
      state.authToken = data.token;
      state.currentUser = data.user;
      localStorage.setItem("census_token", data.token);
      localStorage.setItem("census_user", JSON.stringify(data.user));
      showAppShell();
      updateUserHeader();
      applyRoleBasedNav();
      navigateTo("admin");
      showToast("Signed in as Administrator.");
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
    appendChatMessage("ai", data.answer, data.citations, data.intent);
  } catch (err) {
    removeChatSkeleton(thinkingId);
    appendChatMessage("ai", "I encountered a connection error. Please check your network or try again.", []);
  }
}

function quickAsk(text) {
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

function appendChatMessage(sender, text, citations = [], intent = "") {
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
    const citationHtml = citations && citations.length > 0 
      ? `<div class="flex items-center gap-1 text-[11px] text-outline mt-2.5">
           <span class="material-symbols-outlined text-[13px]">database</span>
           <span>Source: ${escapeHtml(citations.join(" | "))}</span>
         </div>`
      : "";

    msgDiv.innerHTML = `
      <div class="flex items-start gap-3 max-w-[95%] md:max-w-[80%]">
        <div class="w-8 h-8 rounded-full bg-primary-container text-white flex items-center justify-center shrink-0 mt-1">
          <span class="material-symbols-outlined text-lg">smart_toy</span>
        </div>
        <div class="flex flex-col gap-1 flex-1">
          <div class="bg-surface-container-lowest text-on-surface rounded-2xl rounded-tl-sm p-4 shadow-sm border border-outline-variant/30 text-sm leading-relaxed">
            ${formatMarkdown(text)}
            ${citationHtml}
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
      <span class="text-xs text-on-surface-variant font-medium ml-1">Consulting census records...</span>
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

  ["all", "name", "mobile", "id", "hlb"].forEach(f => {
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

    data.results.forEach(rec => {
      const card = document.createElement("article");
      card.className = "bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:bg-surface-container-low transition-all";
      
      const cleanMob = (rec.mobile || "8453441975").replace(/[^0-9]/g, "");
      const waMsg = `Inquiry regarding ${rec.name}${rec.hlb_number ? ` (HLB ${rec.hlb_number})` : ""}`;
      const mapsLinkHtml = rec.maps_url
        ? `<a href="${escapeAttr(rec.maps_url)}" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-primary hover:underline"><span class="material-symbols-outlined text-[15px]">map</span> ${escapeHtml(rec.area_name || "View Area")}</a>`
        : "";

      card.innerHTML = `
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <h3 class="text-base font-bold text-on-surface">${escapeHtml(rec.name)}</h3>
            <span class="text-[10px] px-2 py-0.5 rounded bg-primary-fixed text-primary font-semibold">${escapeHtml(rec.role)}</span>
          </div>
          <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-on-surface-variant mt-1.5">
            <span class="flex items-center gap-1"><span class="material-symbols-outlined text-[15px]">tag</span> HLB: <strong>${escapeHtml(rec.hlb_number || "—")}</strong></span>
            <span class="flex items-center gap-1"><span class="material-symbols-outlined text-[15px]">badge</span> ID: <code class="font-mono">${escapeHtml(rec.user_id)}</code></span>
            <span class="flex items-center gap-1"><span class="material-symbols-outlined text-[15px]">supervisor_account</span> Supervisor: ${escapeHtml(rec.supervisor || "—")}</span>
            <span class="flex items-center gap-1"><span class="material-symbols-outlined text-[15px]">pin_drop</span> Circle: ${escapeHtml(rec.circle || "—")}</span>
            ${mapsLinkHtml}
          </div>
        </div>
        <div class="flex items-center gap-2 w-full md:w-auto justify-end pt-3 md:pt-0 border-t border-outline-variant/20 md:border-t-0">
          <button onclick="nativeCall('${escapeAttr(cleanMob)}')" class="w-9 h-9 rounded-full bg-surface-container border border-outline-variant/30 flex items-center justify-center text-primary hover:bg-primary hover:text-white transition-colors" title="Call +91 ${escapeHtml(rec.mobile || '8453441975')}">
            <span class="material-symbols-outlined text-[17px]" style="font-variation-settings:'FILL' 1">call</span>
          </button>
          <button onclick="nativeWhatsApp('91${escapeAttr(cleanMob)}', '${escapeAttr(waMsg)}')" class="w-9 h-9 rounded-full bg-surface-container border border-outline-variant/30 flex items-center justify-center text-[#25D366] hover:bg-[#25D366] hover:text-white transition-colors" title="Message on WhatsApp">
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

// ==================== 7. MANUALS & GUIDELINES HANDLERS ====================
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
      sourceEl.innerHTML = `Source: <strong>${best.doc_title}, Page ${best.page_number}</strong>`;
    } else {
      titleEl.textContent = "No Exact Guideline Match";
      bodyEl.textContent = "Please consult the full manuals below or contact Technical Assistant Shahin Sha A. (+91 84534 41975).";
      sourceEl.innerHTML = "Source: Census Operating Manuals";
    }
  } catch (err) {
    bodyEl.textContent = "Error executing manual search.";
  }
}

function openPdfModal(filename) {
  const modal = document.getElementById("modal-pdf");
  const title = document.getElementById("pdf-modal-title");
  const content = document.getElementById("pdf-modal-content");

  title.textContent = filename.includes("FAQ") 
    ? "Census 2027 FAQ Manual for Enumerators & Supervisors" 
    : "House Listing Operations (HLO) Instruction Manual";

  content.innerHTML = `
    <div class="bg-surface p-6 rounded-xl border border-outline-variant/30 space-y-4">
      <div class="flex items-center gap-3 p-3 bg-primary-fixed/20 rounded-lg text-primary text-xs font-semibold">
        <span class="material-symbols-outlined">info</span>
        <span>Offline Indexed Document • 100% Vector & Full-Text Search Enabled</span>
      </div>
      <h4 class="text-base font-bold text-on-surface">Document: ${filename}</h4>
      <p class="text-xs text-on-surface-variant leading-relaxed">
        All pages and sections of this official publication have been indexed into the Census Assistant knowledge repository. 
        You can ask any procedural question directly to the AI Assistant or search specific keywords.
      </p>
      <div class="p-4 bg-surface-container rounded-lg text-xs space-y-2 font-mono">
        <p class="font-bold text-primary">Sample Section Overview:</p>
        <p>• Chapter 1: Introduction to Census 2027 & House Listing Operations</p>
        <p>• Chapter 2: Duties of Enumerators and Charge Supervisors</p>
        <p>• Chapter 3: Definition of Building, Census House, and Household</p>
        <p>• Chapter 4: Form 4B Completion Protocols & Mobile App Sync</p>
      </div>
      <button onclick="quickAsk('What are the key instructions in ${filename}?')" class="w-full py-2.5 bg-primary text-white text-xs font-semibold rounded-full hover:bg-primary-container transition-all">
        Ask AI to Summarize this Document
      </button>
    </div>
  `;
  modal.classList.remove("hidden");
}

function closePdfModal() {
  document.getElementById("modal-pdf").classList.add("hidden");
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
// Replaces the old single hardcoded "S. A. Ahmed" profile: this fetches
// the real, searchable list of supervisors (cross-referenced from both
// the All_Users and HLB Allocation Excel sheets) from /api/records/supervisor.
async function loadSupervisors() {
  const container = document.getElementById("supervisors-list");
  if (!container) return;
  const q = (document.getElementById("supervisor-search-input") || {}).value || "";

  container.innerHTML = `<div class="flex justify-center p-8"><div class="loader-spinner-primary"></div></div>`;

  try {
    const res = await apiFetch(`/api/records/supervisor?q=${encodeURIComponent(q.trim())}`);
    const data = await res.json();
    container.innerHTML = "";

    // Render the two Technical Assistants at the top — they are always
    // reachable regardless of search, since they support every circle.
    const taContainer = document.getElementById("supervisor-tech-assistants");
    if (taContainer && data.technical_assistants) {
      taContainer.innerHTML = data.technical_assistants.map(ta => `
        <div class="bg-surface-container-lowest border border-outline-variant/30 rounded-xl p-4 flex items-center justify-between gap-3">
          <div>
            <p class="text-sm font-bold text-on-surface">${escapeHtml(ta.name)}</p>
            <p class="text-[11px] text-tertiary-container font-semibold uppercase tracking-wide">${escapeHtml(ta.designation)}</p>
            <p class="text-xs text-on-surface-variant mt-0.5">${escapeHtml(ta.phone)}</p>
          </div>
          <a href="${escapeAttr(ta.whatsapp_link)}" target="_blank" rel="noopener noreferrer" class="w-9 h-9 rounded-full bg-[#25D366] text-white flex items-center justify-center shrink-0" title="WhatsApp">
            <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 1;">chat</span>
          </a>
        </div>
      `).join("");
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

    data.supervisors.forEach(sup => {
      const cleanMob = (sup.mobile || "").replace(/[^0-9]/g, "");
      const initials = sup.name ? sup.name.split(" ").filter(Boolean).slice(0, 2).map(p => p[0]).join("").toUpperCase() : "SU";
      const circlesHtml = (sup.circles || []).filter(Boolean).map(c =>
        `<span class="px-2.5 py-1 bg-surface-variant text-on-surface rounded-md text-xs font-semibold border border-outline-variant/40">Circle ${escapeHtml(c)}</span>`
      ).join("") || `<span class="text-xs text-on-surface-variant">No circle on record</span>`;
      const mapsLinkHtml = sup.maps_url
        ? `<a href="${escapeAttr(sup.maps_url)}" target="_blank" rel="noopener noreferrer" class="flex-1 border border-primary text-primary bg-surface-container-lowest h-11 rounded-full font-semibold text-xs flex items-center justify-center gap-2 hover:bg-primary-fixed transition-all active:scale-95">
             <span class="material-symbols-outlined text-lg">map</span><span>View Jurisdiction Area</span>
           </a>`
        : "";

      const card = document.createElement("div");
      card.className = "bg-surface-container-lowest rounded-2xl shadow-sm border border-outline-variant/30 overflow-hidden";
      card.innerHTML = `
        <div class="p-5 flex flex-col sm:flex-row sm:items-center gap-4">
          <div class="w-16 h-16 rounded-full bg-primary-container text-white flex items-center justify-center text-xl font-bold shrink-0">${escapeHtml(initials)}</div>
          <div class="flex-1 min-w-0">
            <h3 class="text-lg font-bold text-on-surface truncate">${escapeHtml(sup.name)}</h3>
            <p class="text-xs text-on-surface-variant mt-0.5">${escapeHtml(sup.mobile || "No mobile on record")} • ID: <code class="font-mono">${escapeHtml(sup.user_id)}</code></p>
            <p class="text-xs text-on-surface-variant mt-0.5">${sup.hlb_count} HLB${sup.hlb_count === 1 ? "" : "s"} allocated${sup.area_name ? " • " + escapeHtml(sup.area_name) : ""}</p>
            <div class="flex flex-wrap gap-1.5 mt-2">${circlesHtml}</div>
          </div>
        </div>
        <div class="px-5 pb-5 flex flex-col sm:flex-row gap-2">
          ${cleanMob ? `
          <a href="https://wa.me/91${escapeAttr(cleanMob)}?text=${encodeURIComponent('Hello ' + sup.name + ', I am reaching out regarding HLB operations.')}" target="_blank" rel="noopener noreferrer"
            class="flex-1 bg-primary text-white h-11 rounded-full font-semibold text-xs flex items-center justify-center gap-2 hover:bg-primary-container transition-all active:scale-95">
            <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 1;">chat</span><span>Message on WhatsApp</span>
          </a>` : ""}
          ${mapsLinkHtml}
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `<p class="text-xs text-error p-4">Error loading supervisors.</p>`;
  }
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
    const latEl = document.getElementById("stat-latency");
    const syncEl = document.getElementById("stat-last-sync");

    if (recEl) recEl.textContent = (data.total_records || 1488).toLocaleString();
    if (queryEl) queryEl.textContent = (data.ai_queries_count || 54012).toLocaleString();
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
    } else {
      showToast(data.error || "Sync failed.");
    }
  } catch (err) {
    showToast("Force sync network request failed.");
  }
}

async function handleExcelUpload(input) {
  const file = input.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  showToast(`Uploading ${file.name}...`);
  try {
    const res = await apiFetch("/api/admin/upload-excel", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message);
      loadAdminStats();
    } else {
      showToast(data.error || "Upload failed.");
    }
  } catch (err) {
    showToast("Excel upload failed.");
  }
  input.value = "";
}

async function handlePdfUpload(input) {
  const file = input.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  showToast(`Uploading and chunking ${file.name}...`);
  try {
    const res = await apiFetch("/api/admin/upload-pdf", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message);
      loadAdminStats();
    } else {
      showToast(data.error || "Upload failed.");
    }
  } catch (err) {
    showToast("PDF upload failed.");
  }
  input.value = "";
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
  let html = escapeHtml(text);
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
