import { initializeApp } from "https://www.gstatic.com/firebasejs/12.11.0/firebase-app.js";
import {
  getAnalytics,
  isSupported as isAnalyticsSupported
} from "https://www.gstatic.com/firebasejs/12.11.0/firebase-analytics.js";
import {
  browserLocalPersistence,
  createUserWithEmailAndPassword,
  getAuth,
  GoogleAuthProvider,
  onAuthStateChanged,
  setPersistence,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateProfile
} from "https://www.gstatic.com/firebasejs/12.11.0/firebase-auth.js";
import { firebaseConfig, isFirebaseConfigured } from "./firebase-config.js";

const AUTH_STATE_EVENT = "tw:auth-state-changed";
const LANGUAGE_EVENT = "tw:language-changed";

let appInstance = null;
let authInstance = null;
let analyticsInstance = null;
let googleProvider = null;
let authReadyPromise = null;
let listenersBound = false;
let authFormBound = false;

const authState = {
  configured: false,
  initialized: false,
  pending: false,
  user: null,
  error: null
};

function translate(key, fallback, replacements = {}) {
  if (typeof window.t === "function") {
    const translated = window.t(key, replacements);
    if (translated && translated !== key) {
      return translated;
    }
  }

  let text = fallback || key;
  Object.entries(replacements).forEach(([name, value]) => {
    text = text.replaceAll(`{${name}}`, String(value));
  });
  return text;
}

function dispatchAuthStateChange() {
  document.dispatchEvent(
    new CustomEvent(AUTH_STATE_EVENT, {
      detail: {
        configured: authState.configured,
        initialized: authState.initialized,
        pending: authState.pending,
        user: authState.user,
        error: authState.error
      }
    })
  );
}

function getInitials(user) {
  const source = (user?.displayName || user?.email || "TW").trim();
  const words = source.split(/[\s@._-]+/).filter(Boolean);
  return words
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "TW";
}

function getDisplayName(user) {
  return user?.displayName || user?.email?.split("@")[0] || "Tokyo Weekend";
}

function getUserSubtitle(user) {
  return user?.email || translate("common.account", "Account");
}

function getSafeRedirectUrl(value) {
  const fallback = getAccountHomeHref();
  if (!value) {
    return fallback;
  }

  try {
    const candidate = new URL(value, window.location.origin);
    if (candidate.origin !== window.location.origin) {
      return fallback;
    }
    return `${candidate.pathname}${candidate.search}${candidate.hash}`;
  } catch (error) {
    return fallback;
  }
}

function getAccountHomeHref() {
  return "/pages/account.html";
}

function buildAuthHref(mode = "signin", redirectOverride = null) {
  const redirect =
    redirectOverride ||
    `${window.location.pathname}${window.location.search}${window.location.hash}`;
  return `/pages/auth.html?mode=${encodeURIComponent(mode)}&redirect=${encodeURIComponent(redirect)}`;
}

function setStatusMessage(message, tone = "neutral") {
  const statusEl = document.getElementById("auth-status");
  if (!statusEl) {
    return;
  }

  if (!message) {
    statusEl.hidden = true;
    statusEl.textContent = "";
    statusEl.className = "tw-auth-status";
    return;
  }

  statusEl.hidden = false;
  statusEl.textContent = message;
  statusEl.className = `tw-auth-status is-${tone}`;
}

function getCurrentMode() {
  const params = new URLSearchParams(window.location.search);
  return params.get("mode") === "signup" ? "signup" : "signin";
}

function setPendingState(pending) {
  authState.pending = pending;

  document.querySelectorAll("[data-auth-submit], [data-auth-provider], [data-auth-mode-button]").forEach((element) => {
    if ("disabled" in element) {
      element.disabled = pending;
    }
  });

  const submitLabel = document.querySelector("[data-auth-submit-label]");
  if (submitLabel) {
    submitLabel.textContent = pending
      ? translate("auth.processing", "Processing...")
      : getCurrentMode() === "signup"
        ? translate("auth.createAccountAction", "Create account")
        : translate("auth.signInAction", "Sign in");
  }

  dispatchAuthStateChange();
}

function setFirebaseLanguage() {
  if (!authInstance) {
    return;
  }

  const language = String(document.documentElement.lang || "en").toLowerCase();
  authInstance.languageCode = language.startsWith("ja")
    ? "ja"
    : language.startsWith("zh")
      ? "zh-CN"
      : "en";
}

function getFirebaseErrorMessage(error) {
  const code = String(error?.code || "");

  switch (code) {
    case "auth/invalid-credential":
    case "auth/wrong-password":
    case "auth/invalid-email":
    case "auth/user-not-found":
      return translate("auth.invalidCredentials", "The email or password was not accepted.");
    case "auth/email-already-in-use":
      return translate("auth.emailInUse", "That email is already registered.");
    case "auth/weak-password":
      return translate("auth.weakPassword", "Use at least 6 characters for your password.");
    case "auth/popup-closed-by-user":
      return translate("auth.popupClosed", "The Google sign-in window was closed before finishing.");
    case "auth/popup-blocked":
      return translate("auth.popupBlocked", "Your browser blocked the Google sign-in popup.");
    case "auth/account-exists-with-different-credential":
      return translate(
        "auth.accountExistsDifferentProvider",
        "That email already exists with a different sign-in method."
      );
    case "auth/too-many-requests":
      return translate("auth.tooManyRequests", "Too many attempts. Please wait a moment and try again.");
    default:
      return error?.message || translate("auth.genericError", "Something went wrong. Please try again.");
  }
}

function renderDesktopGuestState(container) {
  container.innerHTML = `
    <div class="tw-header-auth__actions">
      <a class="tw-header-auth__button tw-header-auth__button--account" data-auth-link="signin" href="${buildAuthHref("signin", getAccountHomeHref())}">
        ${translate("common.account", "Account")}
      </a>
    </div>
  `;
}

function renderDesktopUserState(container, user) {
  container.innerHTML = `
    <div class="tw-account-shell">
      <button type="button" class="tw-account-trigger" data-auth-menu-toggle aria-expanded="false">
        <span class="tw-account-avatar">${getInitials(user)}</span>
        <span class="tw-account-copy">
          <strong>${getDisplayName(user)}</strong>
          <span>${translate("common.account", "Account")}</span>
        </span>
      </button>
      <div class="tw-account-menu" hidden>
        <p class="tw-account-menu__eyebrow">${translate("common.account", "Account")}</p>
        <p class="tw-account-menu__name">${getDisplayName(user)}</p>
        <p class="tw-account-menu__email">${getUserSubtitle(user)}</p>
        <div class="tw-account-menu__actions">
          <a class="tw-account-menu__link" href="${getAccountHomeHref()}">
            ${translate("auth.manageAccount", "Manage account")}
          </a>
          <button type="button" class="tw-account-menu__signout" data-auth-action="signout">
            ${translate("common.signOut", "Sign out")}
          </button>
        </div>
      </div>
    </div>
  `;
}

function renderMobileGuestState(container) {
  container.innerHTML = `
    <div class="tw-mobile-auth__card">
      <p class="tw-mobile-auth__eyebrow">${translate("auth.mobileKicker", "Member access")}</p>
      <p class="tw-mobile-auth__copy">${translate("auth.mobileCopy", "Create an account or sign in to continue with secure access.")}</p>
      <div class="tw-mobile-auth__actions">
        <a class="tw-mobile-auth__button" data-auth-link="signin" href="${buildAuthHref("signin", getAccountHomeHref())}">
          ${translate("common.account", "Account")}
        </a>
      </div>
    </div>
  `;
}

function renderMobileUserState(container, user) {
  container.innerHTML = `
    <div class="tw-mobile-auth__card is-signed-in">
      <div class="tw-mobile-auth__identity">
        <span class="tw-account-avatar">${getInitials(user)}</span>
        <div>
          <p class="tw-mobile-auth__name">${getDisplayName(user)}</p>
          <p class="tw-mobile-auth__email">${getUserSubtitle(user)}</p>
        </div>
      </div>
      <div class="tw-mobile-auth__actions">
        <a class="tw-mobile-auth__link" href="${getAccountHomeHref()}">
          ${translate("auth.manageAccount", "Manage account")}
        </a>
        <button type="button" class="tw-mobile-auth__button" data-auth-action="signout">
          ${translate("common.signOut", "Sign out")}
        </button>
      </div>
    </div>
  `;
}

function renderHeaderAuth() {
  const desktopContainer = document.getElementById("header-auth-desktop");
  const mobileContainer = document.getElementById("header-auth-mobile");

  if (desktopContainer) {
    if (authState.user) {
      renderDesktopUserState(desktopContainer, authState.user);
    } else {
      renderDesktopGuestState(desktopContainer);
    }
  }

  if (mobileContainer) {
    if (authState.user) {
      renderMobileUserState(mobileContainer, authState.user);
    } else {
      renderMobileGuestState(mobileContainer);
    }
  }
}

function closeAccountMenus() {
  document.querySelectorAll(".tw-account-shell").forEach((shell) => {
    const toggle = shell.querySelector("[data-auth-menu-toggle]");
    const menu = shell.querySelector(".tw-account-menu");
    if (toggle) {
      toggle.setAttribute("aria-expanded", "false");
    }
    if (menu) {
      menu.hidden = true;
    }
  });
}

function toggleAccountMenu(button) {
  const shell = button.closest(".tw-account-shell");
  const menu = shell?.querySelector(".tw-account-menu");
  if (!shell || !menu) {
    return;
  }

  const expanded = button.getAttribute("aria-expanded") === "true";
  closeAccountMenus();
  if (!expanded) {
    button.setAttribute("aria-expanded", "true");
    menu.hidden = false;
  }
}

function getRedirectTarget() {
  const params = new URLSearchParams(window.location.search);
  return getSafeRedirectUrl(params.get("redirect"));
}

function applyMode(mode) {
  const normalizedMode = mode === "signup" ? "signup" : "signin";
  const root = document.querySelector("[data-auth-shell]");
  if (!root) {
    return;
  }

  root.dataset.authMode = normalizedMode;

  document.querySelectorAll("[data-auth-mode-button]").forEach((button) => {
    const active = button.dataset.authModeButton === normalizedMode;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  const nameField = document.querySelector("[data-auth-name-field]");
  if (nameField) {
    nameField.hidden = normalizedMode !== "signup";
  }

  const confirmField = document.querySelector("[data-auth-confirm-field]");
  if (confirmField) {
    confirmField.hidden = normalizedMode !== "signup";
  }

  const submitLabel = document.querySelector("[data-auth-submit-label]");
  if (submitLabel) {
    submitLabel.textContent = normalizedMode === "signup"
      ? translate("auth.createAccountAction", "Create account")
      : translate("auth.signInAction", "Sign in");
  }

  const helper = document.querySelector("[data-auth-helper]");
  if (helper) {
    helper.textContent = normalizedMode === "signup"
      ? translate("auth.signupHelper", "Use email and password to create a secure account.")
      : translate("auth.signinHelper", "Sign in with the account you already created.");
  }

  const url = new URL(window.location.href);
  url.searchParams.set("mode", normalizedMode);
  window.history.replaceState({}, "", url);
  setStatusMessage("");
}

function renderAuthSetupState() {
  const form = document.getElementById("auth-form");
  const success = document.getElementById("auth-signed-in");
  const setup = document.getElementById("auth-setup-notice");

  if (!form || !success || !setup) {
    return;
  }

  setup.hidden = authState.configured;
  form.hidden = !authState.configured || Boolean(authState.user);
  success.hidden = !authState.user;

  if (authState.user) {
    const nameEl = document.getElementById("auth-user-name");
    const emailEl = document.getElementById("auth-user-email");
    const continueLink = document.getElementById("auth-continue-link");

    if (nameEl) {
      nameEl.textContent = getDisplayName(authState.user);
    }
    if (emailEl) {
      emailEl.textContent = getUserSubtitle(authState.user);
    }
    if (continueLink) {
      continueLink.href = getRedirectTarget();
    }
  }
}

async function handleEmailAuthSubmit(event) {
  event.preventDefault();
  if (!authInstance || !authState.configured) {
    return;
  }

  const formData = new FormData(event.currentTarget);
  const mode = getCurrentMode();
  const name = String(formData.get("name") || "").trim();
  const email = String(formData.get("email") || "").trim();
  const password = String(formData.get("password") || "");
  const confirmPassword = String(formData.get("confirmPassword") || "");

  if (!email || !password) {
    setStatusMessage(translate("auth.fillRequired", "Please fill in your email and password."), "error");
    return;
  }

  if (mode === "signup") {
    if (!name) {
      setStatusMessage(translate("auth.nameRequired", "Add a display name to finish creating your account."), "error");
      return;
    }
    if (password.length < 6) {
      setStatusMessage(translate("auth.weakPassword", "Use at least 6 characters for your password."), "error");
      return;
    }
    if (password !== confirmPassword) {
      setStatusMessage(translate("auth.passwordMismatch", "Your password confirmation does not match."), "error");
      return;
    }
  }

  setPendingState(true);
  setStatusMessage("");

  try {
    if (mode === "signup") {
      const credential = await createUserWithEmailAndPassword(authInstance, email, password);
      if (name) {
        await updateProfile(credential.user, { displayName: name });
      }
      authState.user = authInstance.currentUser;
      setStatusMessage(translate("auth.accountCreated", "Your account is ready."), "success");
    } else {
      await signInWithEmailAndPassword(authInstance, email, password);
      setStatusMessage(translate("auth.signedIn", "You are signed in."), "success");
    }
  } catch (error) {
    authState.error = error;
    setStatusMessage(getFirebaseErrorMessage(error), "error");
  } finally {
    setPendingState(false);
    renderAuthSetupState();
    renderHeaderAuth();
  }
}

async function handleGoogleSignIn() {
  if (!authInstance || !googleProvider || !authState.configured) {
    return;
  }

  setPendingState(true);
  setStatusMessage("");

  try {
    await signInWithPopup(authInstance, googleProvider);
    setStatusMessage(translate("auth.googleSuccess", "Google sign-in completed."), "success");
  } catch (error) {
    authState.error = error;
    setStatusMessage(getFirebaseErrorMessage(error), "error");
  } finally {
    setPendingState(false);
    renderAuthSetupState();
    renderHeaderAuth();
  }
}

async function signOutCurrentUser() {
  if (!authInstance) {
    return;
  }

  try {
    await signOut(authInstance);
    closeAccountMenus();
    setStatusMessage(translate("auth.signedOut", "You have signed out."), "success");
  } catch (error) {
    setStatusMessage(getFirebaseErrorMessage(error), "error");
  } finally {
    renderAuthSetupState();
    renderHeaderAuth();
  }
}

function mountAuthPage() {
  const shell = document.querySelector("[data-auth-shell]");
  if (!shell) {
    return;
  }

  if (!authFormBound) {
    const form = document.getElementById("auth-form");
    if (form) {
      form.addEventListener("submit", handleEmailAuthSubmit);
    }

    document.querySelectorAll("[data-auth-mode-button]").forEach((button) => {
      button.addEventListener("click", () => applyMode(button.dataset.authModeButton));
    });

    const googleButton = document.querySelector("[data-auth-provider='google']");
    if (googleButton) {
      googleButton.addEventListener("click", handleGoogleSignIn);
    }

    const signOutButton = document.getElementById("auth-page-signout");
    if (signOutButton) {
      signOutButton.addEventListener("click", async () => {
        await signOutCurrentUser();
      });
    }

    authFormBound = true;
  }

  applyMode(getCurrentMode());
  renderAuthSetupState();

  if (!authState.configured) {
    setStatusMessage(
      translate(
        "auth.setupMessage",
        "Firebase Auth is wired in, but the project configuration in Js/firebase-config.js still needs your real Firebase web app values."
      ),
      "warning"
    );
  }
}

function bindListeners() {
  if (listenersBound) {
    return;
  }

  listenersBound = true;

  document.addEventListener("click", async (event) => {
    const signOutButton = event.target.closest("[data-auth-action='signout']");
    if (signOutButton) {
      event.preventDefault();
      await signOutCurrentUser();
      return;
    }

    const menuToggle = event.target.closest("[data-auth-menu-toggle]");
    if (menuToggle) {
      event.preventDefault();
      toggleAccountMenu(menuToggle);
      return;
    }

    if (!event.target.closest(".tw-account-shell")) {
      closeAccountMenus();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeAccountMenus();
    }
  });

  document.addEventListener(LANGUAGE_EVENT, () => {
    setFirebaseLanguage();
    renderHeaderAuth();
    mountAuthPage();
  });

  document.addEventListener(AUTH_STATE_EVENT, () => {
    renderHeaderAuth();
    renderAuthSetupState();
  });
}

async function initFirebaseAuth() {
  if (authReadyPromise) {
    return authReadyPromise;
  }

  bindListeners();
  authState.configured = isFirebaseConfigured(firebaseConfig);

  window.TWAuth = {
    renderHeaderAuth,
    mountAuthPage,
    buildAuthHref,
    signOutCurrentUser,
    getState() {
      return {
        ...authState,
        analyticsEnabled: Boolean(analyticsInstance)
      };
    }
  };

  authReadyPromise = (async () => {
    if (!authState.configured) {
      authState.initialized = true;
      dispatchAuthStateChange();
      return;
    }

    appInstance = initializeApp(firebaseConfig);
    if (firebaseConfig.measurementId && (await isAnalyticsSupported())) {
      analyticsInstance = getAnalytics(appInstance);
    }
    authInstance = getAuth(appInstance);
    googleProvider = new GoogleAuthProvider();
    googleProvider.setCustomParameters({ prompt: "select_account" });
    setFirebaseLanguage();

    await setPersistence(authInstance, browserLocalPersistence);

    onAuthStateChanged(authInstance, (user) => {
      authState.user = user;
      authState.initialized = true;
      authState.error = null;
      dispatchAuthStateChange();
      renderHeaderAuth();
      renderAuthSetupState();
    });
  })().catch((error) => {
    authState.initialized = true;
    authState.error = error;
    dispatchAuthStateChange();
    console.error("Firebase auth initialization failed.", error);
  });

  return authReadyPromise;
}

export async function bootstrapPage(pageName) {
  await initFirebaseAuth();
  await window.initializePage(pageName);
  renderHeaderAuth();
  mountAuthPage();
}
