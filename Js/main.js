const LANGUAGE_STORAGE_KEY = "tokyoWeekendLanguage";
const DEFAULT_LANGUAGE = "en";

const UI_STRINGS = {
  en: {
    meta: {
      homeTitle: "Things to Do in Tokyo This Weekend",
      filmTitle: "Tokyo Film Guide",
      exhibitionsTitle: "Tokyo Exhibitions",
      nightlifeTitle: "Tokyo Nightlife",
      activitiesTitle: "Tokyo Activities",
      authTitle: "Sign In | Tokyo Weekend",
      accountTitle: "My Calendar | Tokyo Weekend",
      allTitle: "All listings | Tokyo Weekend",
      aboutTitle: "About | Tokyo Weekend",
      contactTitle: "Contact | Tokyo Weekend",
      eventSuffix: "Tokyo Weekend"
    },
    nav: {
      home: "Home",
      film: "Film",
      exhibitions: "Exhibitions",
      nightlife: "Nightlife",
      activities: "Activities"
    },
    common: {
      openMenu: "Open menu",
      closeMenu: "Close menu",
      languageSwitcher: "Language",
      signIn: "Sign in",
      createAccount: "Create account",
      account: "Account",
      signOut: "Sign out",
      follow: "Follow",
      about: "About",
      contact: "Contact",
      footer: "Tokyo Weekend Guide © 2026",
      viewAll: "View all",
      thisWeekend: "This weekend",
      datesNotListed: "Dates not listed",
      filmDatesUnconfirmed: "Screening dates were not provided, so this title is not listed as now showing.",
      eventEndedOn: "This event ended on {date}.",
      noWeekendEvents: "No confirmed events this weekend.",
      noConfirmedFilms: "No films with a confirmed screening date. Titles that only say “now showing” are hidden.",
      viewDetails: "View details ->",
      visitSource: "Visit source ->",
      noEvents: "No events found.",
      loadEventsError: "Failed to load events.",
      noTopPicks: "No top picks available.",
      loadTopPicksError: "Failed to load top picks.",
      unknownSource: "Unknown",
      eventNotFound: "Event not found",
      eventLoadError: "Failed to load event",
      statusLabel: "Status",
      nowShowing: "Now showing",
      basedOnReviews: "Based on 128 reviews",
      outOfFive: "out of 5"
    },
    home: {
      heroTitle: "What to Do in Tokyo This Weekend",
      heroSubtitle: "Find film screenings, exhibitions, nightlife and useful event picks in Tokyo.",
      searchPlaceholder: "Search events...",
      topPicksTitle: "Top Picks This Weekend",
      searchResults: "Search results"
    },
    filmPage: {
      intro: "Only films with a confirmed screening end date are listed. A title that only says “now showing” is not treated as current."
    },
    all: {
      title: "All current listings",
      intro: "Ended events are hidden. Films without a screening end date are hidden too."
    },
    about: {
      title: "About Tokyo Weekend",
      lead: "Tokyo Weekend is a small guide to films, exhibitions, nightlife, and city activities. Listings are collected from public museum, cinema, and event pages, then shortened for the site.",
      dates: "An event with an end date before today is hidden. A film that only says “now showing”, with no end date, is not labeled as currently showing. “This weekend” means Friday through Sunday of the current week, and only events whose dates overlap that window.",
      sources: "Dates, venues, and ticket links come from the source pages. The short summaries are editorial text. This site does not invent visitor scores or reviews.",
      contactLink: "Contact"
    },
    contact: {
      title: "Contact",
      lead: "For corrections, missing dates, or partnership notes, email the owner.",
      note: "This address is the site owner’s contact email."
    },
    auth: {
      kicker: "Member access",
      title: "Make your Tokyo weekend feel a little more personal.",
      subtitle: "Use email or Google to create a secure account that carries across visits.",
      benefitOneTitle: "Fast return access",
      benefitOneBody: "Come back without repeating the same setup every time you browse plans.",
      benefitTwoTitle: "Google in one step",
      benefitTwoBody: "Use your Google account when you want the quickest path in.",
      benefitThreeTitle: "Ready for member features",
      benefitThreeBody: "Your account foundation is ready for future saved picks and personalized tools.",
      panelEyebrow: "Account",
      signInTab: "Sign in",
      createAccountTab: "Create account",
      signinHelper: "Sign in with the account you already created.",
      signupHelper: "Use email and password to create a secure account.",
      setupTitle: "Firebase configuration needed",
      setupBody: "Add your Firebase web app config to Js/firebase-config.js, then enable Email/Password and Google in the Firebase console.",
      nameLabel: "Display name",
      namePlaceholder: "Your name",
      emailLabel: "Email",
      emailPlaceholder: "you@example.com",
      passwordLabel: "Password",
      passwordPlaceholder: "Minimum 6 characters",
      confirmPasswordLabel: "Confirm password",
      confirmPasswordPlaceholder: "Repeat your password",
      signInAction: "Sign in",
      createAccountAction: "Create account",
      orContinueWith: "Or continue with",
      googleAction: "Continue with Google",
      processing: "Processing...",
      signedInEyebrow: "Signed in",
      continueAction: "Continue",
      invalidCredentials: "The email or password was not accepted.",
      emailInUse: "That email is already registered.",
      weakPassword: "Use at least 6 characters for your password.",
      popupClosed: "The Google sign-in window was closed before finishing.",
      popupBlocked: "Your browser blocked the Google sign-in popup.",
      accountExistsDifferentProvider: "That email already exists with a different sign-in method.",
      tooManyRequests: "Too many attempts. Please wait a moment and try again.",
      genericError: "Something went wrong. Please try again.",
      mobileKicker: "Member access",
      mobileCopy: "Create an account or sign in to continue with secure access.",
      manageAccount: "Manage account",
      fillRequired: "Please fill in your email and password.",
      nameRequired: "Add a display name to finish creating your account.",
      passwordMismatch: "Your password confirmation does not match.",
      accountCreated: "Your account is ready.",
      signedIn: "You are signed in.",
      googleSuccess: "Google sign-in completed.",
      signedOut: "You have signed out.",
      setupMessage: "Firebase Auth is wired in, but the project configuration in Js/firebase-config.js still needs your real Firebase web app values."
    },
    accountHome: {
      eyebrow: "Personal planner",
      title: "My Weekend Calendar",
      subtitle: "Preview only. This calendar does not save plans, and it does not show sample events.",
      previewBanner: "Preview only. Nothing on this calendar is saved, and the old sample dates have been removed.",
      monthLabel: "Calendar",
      todayAction: "Today",
      selectedDayTitle: "Selected day",
      linkedActivitiesTitle: "Linked activities",
      linkingReady: "Preview only",
      linkingReadyBody: "Signing in does not save plans. Nothing on this calendar is stored.",
      guestTitle: "Preview calendar",
      guestBody: "You can look through the month. Saving plans is not available.",
      signInAction: "Sign in to continue",
      noActivities: "No saved plans.",
      noActivitiesBody: "This preview does not store events on a day.",
      placeholderBadge: "Coming soon",
      ideasTitle: "What this page will support later",
      ideasOne: "Attach screenings, exhibitions, nightlife plans, and activities to exact dates.",
      ideasTwo: "Keep a clear day-by-day view of what is confirmed and what is still just an idea.",
      ideasThree: "Use the side panel for notes, saved combinations, and quick planning context.",
      scheduleTitle: "Daily structure",
      scheduleMorning: "Morning",
      scheduleAfternoon: "Afternoon",
      scheduleEvening: "Evening",
      scheduleEmpty: "No plan yet",
      markerSingle: "1 plan",
      markerPlural: "{count} plans"
    },
    event: {
      highlights: "Highlights",
      visitorRating: "Visitor rating",
      aboutEvent: "About this event",
      filmSynopsis: "Film synopsis"
    },
    categories: {
      exhibition: "Exhibition",
      film: "Film",
      nightlife: "Nightlife",
      activity: "Activities"
    }
  },
  ja: {
    meta: {
      homeTitle: "今週末の東京ガイド",
      filmTitle: "東京映画ガイド",
      exhibitionsTitle: "東京の展覧会",
      nightlifeTitle: "東京ナイトライフ",
      activitiesTitle: "東京アクティビティ",
      eventSuffix: "Tokyo Weekend"
    },
    nav: {
      home: "ホーム",
      film: "映画",
      exhibitions: "展覧会",
      nightlife: "ナイトライフ",
      activities: "アクティビティ"
    },
    common: {
      openMenu: "メニューを開く",
      closeMenu: "メニューを閉じる",
      languageSwitcher: "言語",
      follow: "フォロー",
      about: "このサイトについて",
      contact: "お問い合わせ",
      footer: "Tokyo Weekend Guide © 2026",
      viewAll: "すべて見る",
      thisWeekend: "今週末",
      datesNotListed: "日付の記載なし",
      filmDatesUnconfirmed: "上映終了日がないため、上映中としては載せていません。",
      eventEndedOn: "このイベントは {date} に終了しました。",
      noWeekendEvents: "今週末で日付が確認できたイベントはありません。",
      noConfirmedFilms: "上映終了日が確認できた映画はありません。「上映中」とだけ書かれた作品は載せていません。",
      viewDetails: "詳細を見る ->",
      visitSource: "公式を見る ->",
      noEvents: "イベントが見つかりません。",
      loadEventsError: "イベントを読み込めませんでした。",
      noTopPicks: "注目イベントはまだありません。",
      loadTopPicksError: "注目イベントを読み込めませんでした。",
      unknownSource: "不明",
      eventNotFound: "イベントが見つかりません。",
      eventLoadError: "イベントを読み込めませんでした。",
      statusLabel: "上映状況",
      nowShowing: "上映中",
      basedOnReviews: "128件のレビューに基づく",
      outOfFive: "5点満点"
    },
    home: {
      heroTitle: "今週末、東京で何をする？",
      heroSubtitle: "映画、展覧会、ナイトライフ、週末向けのおすすめイベントをまとめて探せます。",
      searchPlaceholder: "イベントを検索...",
      topPicksTitle: "今週末の注目イベント",
      searchResults: "検索結果"
    },
    filmPage: {
      intro: "上映終了日が確認できた映画だけを掲載します。「上映中」とだけ書かれた作品は、現在上映中とは扱いません。"
    },
    all: {
      title: "掲載中の一覧",
      intro: "終了日を過ぎたイベントは表示しません。上映終了日がない映画も表示しません。"
    },
    about: {
      title: "Tokyo Weekend について",
      lead: "映画、展覧会、ナイトライフ、街のイベントを、公開ページから集めて短くまとめたガイドです。",
      dates: "終了日が今日より前のイベントは隠し、「上映中」としか書かれていない映画は上映中とは表示しません。「今週末」は今週の金曜から日曜で、その期間と日付が重なるものだけです。",
      sources: "日付、会場、チケットリンクは出典ページのものです。短い紹介文は編集文です。来場者スコアやレビューは作っていません。",
      contactLink: "お問い合わせ"
    },
    contact: {
      title: "お問い合わせ",
      lead: "訂正、日付の抜け、提携については所有者にメールしてください。",
      note: "このアドレスはサイト所有者の連絡先です。"
    },
    event: {
      highlights: "見どころ",
      visitorRating: "来場者評価",
      aboutEvent: "イベント紹介",
      filmSynopsis: "映画紹介"
    },
    categories: {
      exhibition: "展覧会",
      film: "映画",
      nightlife: "ナイトライフ",
      activity: "アクティビティ"
    }
  },
  zh: {
    meta: {
      homeTitle: "东京周末指南",
      filmTitle: "东京电影推荐",
      exhibitionsTitle: "东京展览推荐",
      nightlifeTitle: "东京夜生活推荐",
      activitiesTitle: "东京活动推荐",
      eventSuffix: "Tokyo Weekend"
    },
    nav: {
      home: "首页",
      film: "电影",
      exhibitions: "展览",
      nightlife: "夜生活",
      activities: "活动"
    },
    common: {
      openMenu: "打开菜单",
      closeMenu: "关闭菜单",
      languageSwitcher: "语言",
      follow: "关注",
      about: "关于",
      contact: "联系",
      footer: "Tokyo Weekend Guide © 2026",
      viewAll: "查看全部",
      thisWeekend: "本周末",
      datesNotListed: "未提供日期",
      filmDatesUnconfirmed: "没有放映结束日期，因此不会标成正在上映。",
      eventEndedOn: "这个活动已于 {date} 结束。",
      noWeekendEvents: "本周末没有日期已确认的活动。",
      noConfirmedFilms: "没有带确认放映日期的电影。只写着“正在上映”的条目已隐藏。",
      viewDetails: "查看详情 ->",
      visitSource: "查看来源 ->",
      noEvents: "暂无相关内容。",
      loadEventsError: "加载活动失败。",
      noTopPicks: "暂无精选推荐。",
      loadTopPicksError: "加载精选推荐失败。",
      unknownSource: "未知",
      eventNotFound: "未找到该活动。",
      eventLoadError: "活动加载失败。",
      statusLabel: "状态",
      nowShowing: "正在上映",
      basedOnReviews: "基于 128 条评论",
      outOfFive: "满分 5 分"
    },
    home: {
      heroTitle: "这个周末在东京做什么？",
      heroSubtitle: "快速找到东京的电影、展览、夜生活和实用活动推荐。",
      searchPlaceholder: "搜索活动...",
      topPicksTitle: "本周末精选",
      searchResults: "搜索结果"
    },
    filmPage: {
      intro: "只列出有确认放映结束日期的电影。只写着“正在上映”的片名不会被当成当前在映。"
    },
    all: {
      title: "当前列表",
      intro: "已结束的活动不显示。没有放映结束日期的电影也不显示。"
    },
    about: {
      title: "关于 Tokyo Weekend",
      lead: "这是一份东京电影、展览、夜生活和城市活动的小型指南。条目来自公开页面，再压缩成短介绍。",
      dates: "结束日期早于今天的活动会被隐藏。只写着“正在上映”、没有结束日期的电影不会被标成正在上映。“本周末”指本周五到周日，并且只保留日期与这段时间重叠的活动。",
      sources: "日期、场馆和购票链接来自原始页面。短介绍是编辑文字。本站不编造访客评分或评论。",
      contactLink: "联系"
    },
    contact: {
      title: "联系",
      lead: "更正、缺日期或合作事宜，请发邮件给站主。",
      note: "这个地址是站主的联系邮箱。"
    },
    event: {
      highlights: "推荐亮点",
      visitorRating: "访客评分",
      aboutEvent: "活动介绍",
      filmSynopsis: "电影简介"
    },
    categories: {
      exhibition: "展览",
      film: "电影",
      nightlife: "夜生活",
      activity: "活动"
    }
  }
};

function getEventsJsonPath() {
  return "/data/generated_events.json";
}

function normalizeLanguage(language) {
  const text = (language || "").toLowerCase();
  if (text.startsWith("ja")) return "ja";
  if (text.startsWith("zh")) return "zh";
  return "en";
}

function getCurrentLanguage() {
  try {
    return normalizeLanguage(localStorage.getItem(LANGUAGE_STORAGE_KEY) || DEFAULT_LANGUAGE);
  } catch (error) {
    return DEFAULT_LANGUAGE;
  }
}

function setCurrentLanguage(language) {
  const nextLanguage = normalizeLanguage(language);
  try {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, nextLanguage);
  } catch (error) {
    console.warn("Failed to persist language preference.", error);
  }
  document.documentElement.lang = nextLanguage;
}

function getTranslationValue(language, key) {
  return key.split(".").reduce((accumulator, segment) => accumulator?.[segment], UI_STRINGS[language]);
}

function t(key, replacements = {}) {
  const language = getCurrentLanguage();
  let template =
    getTranslationValue(language, key) ??
    getTranslationValue(DEFAULT_LANGUAGE, key) ??
    key;

  Object.entries(replacements).forEach(([name, value]) => {
    template = template.replaceAll(`{${name}}`, value);
  });

  return template;
}

async function loadEvents() {
  const res = await fetch(getEventsJsonPath());
  if (!res.ok) {
    throw new Error("Failed to load events.json");
  }
  return await res.json();
}

function getBasePath() {
  return "/";
}

function generateSlug(text) {
  return (text || "")
    .toLowerCase()
    .trim()
    .replace(/&/g, " and ")
    .replace(/[^\w\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function escapeHtml(text) {
  return (text || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function hasRealImage(item) {
  const image = (item?.image || "").trim().toLowerCase();
  if (!image) {
    return false;
  }

  return ![
    "no_image",
    "noimage",
    "sakuhin_nothing",
    "comingsoon_noimg"
  ].some((pattern) => image.includes(pattern));
}

function getCategoryKey(item) {
  return (item?.category || "").toLowerCase();
}

function localizeCategory(category) {
  const normalized = (category || "").toLowerCase();
  if (normalized === "exhibition") return t("categories.exhibition");
  if (normalized === "film") return t("categories.film");
  if (normalized === "nightlife") return t("categories.nightlife");
  if (normalized === "activity") return t("categories.activity");
  return category || "";
}

function localizeRuntimeText(text) {
  if (!text) return "";
  if ((text || "").trim().toLowerCase() === "now showing") {
    return t("common.datesNotListed");
  }
  return text;
}

function getLocalizedEventValue(event, field) {
  const language = getCurrentLanguage();
  const translationPack = event?.translations?.[language];
  return translationPack?.[field] ?? event?.[field];
}

function getLocalizedEventArray(event, field) {
  const value = getLocalizedEventValue(event, field);
  return Array.isArray(value) ? value : safeArray(event?.[field]);
}

function getDisplayEvent(event) {
  return {
    ...event,
    title: getLocalizedEventValue(event, "title") || event.title || "",
    summary: getLocalizedEventValue(event, "summary") || event.summary || "",
    description: getLocalizedEventArray(event, "description"),
    highlights: getLocalizedEventArray(event, "highlights"),
    location: getLocalizedEventValue(event, "location") || event.location || "",
    venue: getLocalizedEventValue(event, "venue") || event.venue || "",
    access: getLocalizedEventValue(event, "access") || event.access || "",
    date: localizeRuntimeText(getLocalizedEventValue(event, "date") || event.date || ""),
    categoryLabel: localizeCategory(event.category || "")
  };
}

function createSvgPlaceholder(item) {
  const category = getCategoryKey(item);
  const title = (item?.title || "Tokyo Weekend")
    .replace(/[&<>"']/g, "")
    .slice(0, 52);

  let palette = {
    background: "#f3f4f6",
    accent: "#111827",
    sub: "#6b7280",
    label: "TOKYO WEEKEND"
  };

  if (category === "film") {
    palette = {
      background: "#111827",
      accent: "#f8fafc",
      sub: "#f87171",
      label: "FILM"
    };
  } else if (category === "nightlife") {
    palette = {
      background: "#111111",
      accent: "#fb923c",
      sub: "#fdba74",
      label: "NIGHTLIFE"
    };
  } else if (category === "activity") {
    palette = {
      background: "#fef3c7",
      accent: "#1f2937",
      sub: "#b45309",
      label: "TOKYO ACTIVITY"
    };
  }

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 700">
      <rect width="1200" height="700" fill="${palette.background}" />
      <text x="60" y="120" fill="${palette.sub}" font-family="Arial, sans-serif" font-size="34" font-weight="700" letter-spacing="6">${palette.label}</text>
      <text x="60" y="280" fill="${palette.accent}" font-family="Arial, sans-serif" font-size="76" font-weight="700">${title}</text>
      <rect x="60" y="500" width="300" height="14" rx="7" fill="${palette.sub}" opacity="0.5" />
      <rect x="60" y="540" width="430" height="14" rx="7" fill="${palette.sub}" opacity="0.28" />
      <circle cx="1020" cy="120" r="64" fill="${palette.sub}" opacity="0.18" />
      <circle cx="950" cy="560" r="120" fill="${palette.sub}" opacity="0.12" />
    </svg>
  `;

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function getCardMeta(item) {
  const category = getCategoryKey(item);

  if (category === "film") {
    const locationText = (item.location || "").trim();
    return locationText || item.date || "";
  }

  return `${(item.location || "").trim()}${item.date ? ` - ${item.date}` : ""}`;
}

function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function parseIsoDate(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || "").trim());
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(year, month - 1, day);
  if (date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day) {
    return null;
  }
  return date;
}

function dateFromParts(year, monthIndex, day) {
  const date = new Date(year, monthIndex, day);
  if (date.getFullYear() !== year || date.getMonth() !== monthIndex || date.getDate() !== day) {
    return null;
  }
  return date;
}

function monthIndex(name) {
  const months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];
  return months.indexOf(String(name || "").toLowerCase());
}

function parseChunk(chunk, fallbackYear) {
  const dotted = String(chunk || "").match(/(\d{4})\.(\d{1,2})\.(\d{1,2})/);
  if (dotted) return dateFromParts(Number(dotted[1]), Number(dotted[2]) - 1, Number(dotted[3]));

  const short = String(chunk || "").match(/(?:^|[^\d])(\d{1,2})\.(\d{1,2})(?!\d)/);
  if (short && fallbackYear) return dateFromParts(fallbackYear, Number(short[1]) - 1, Number(short[2]));

  const named = String(chunk || "").match(/(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,)?(?:\s*\([^)]*\))?(?:,)?\s*(\d{4})?/i);
  if (!named) return null;
  const year = named[3] ? Number(named[3]) : fallbackYear;
  const month = monthIndex(named[1]);
  if (!year || month < 0) return null;
  return dateFromParts(year, month, Number(named[2]));
}

function parseDisplayRange(text) {
  const raw = String(text || "").trim();
  const lower = raw.toLowerCase();
  if (!raw || lower === "see source" || lower === "now showing") {
    return { start: null, end: null };
  }

  const parts = raw.split(/\s*[–—-]\s*/);
  const years = (raw.match(/\d{4}/g) || []).map(Number);
  const fallback = years[0] || null;
  if (parts.length === 1) {
    return { start: null, end: parseChunk(parts[0], fallback) };
  }

  const start = parseChunk(parts[0], fallback);
  let end = parseChunk(parts[parts.length - 1], start ? start.getFullYear() : (years[years.length - 1] || null));
  if (start && end && end < start && !/\d{4}/.test(parts[parts.length - 1])) {
    end = dateFromParts(end.getFullYear() + 1, end.getMonth(), end.getDate());
  }
  return { start, end };
}

function effectiveRange(event) {
  const isoStart = parseIsoDate(event?.startDate);
  const isoEnd = parseIsoDate(event?.endDate);
  if (isoStart || isoEnd) return { start: isoStart, end: isoEnd };
  return parseDisplayRange(event?.date);
}

function isEnded(event, today = startOfDay(new Date())) {
  const end = effectiveRange(event).end;
  if (!end) return false;
  return startOfDay(end) < today;
}

function isUndatedNowShowingFilm(event) {
  if (getCategoryKey(event) !== "film") return false;
  if (parseIsoDate(event?.endDate)) return false;
  const label = String(event?.date || "").trim().toLowerCase();
  return label === "" || label === "now showing";
}

function isListable(event) {
  if (!hasRealImage(event)) return false;
  if (isEnded(event)) return false;
  if (isUndatedNowShowingFilm(event)) return false;
  return true;
}

function thisWeekendRange(today = startOfDay(new Date())) {
  const day = today.getDay();
  const friday = new Date(today);
  friday.setDate(today.getDate() + (day === 0 ? -2 : 5 - day));
  const sunday = new Date(friday);
  sunday.setDate(friday.getDate() + 2);
  return { start: startOfDay(friday), end: startOfDay(sunday) };
}

function overlapsThisWeekend(event, today = startOfDay(new Date())) {
  const range = effectiveRange(event);
  if (!range.end) return false;
  const start = range.start || new Date(0);
  const weekend = thisWeekendRange(today);
  return startOfDay(start) <= weekend.end && startOfDay(range.end) >= weekend.start;
}

function compareRank(a, b) {
  const popularity = (Number(b.popularityScore) || 0) - (Number(a.popularityScore) || 0);
  if (popularity) return popularity;
  const quality = (Number(b.qualityScore) || 0) - (Number(a.qualityScore) || 0);
  if (quality) return quality;
  return String(a.title || "").localeCompare(String(b.title || ""));
}

function formatIsoDate(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return "";
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function endedLabel(event) {
  const end = effectiveRange(event).end;
  return t("common.eventEndedOn", { date: formatIsoDate(end) || event.endDate || event.date || "" });
}

function availabilityMessage(event) {
  if (isEnded(event)) {
    return endedLabel(event);
  }
  if (isUndatedNowShowingFilm(event)) {
    return t("common.filmDatesUnconfirmed");
  }
  return "";
}

function safeUrl(value) {
  try {
    const parsed = new URL(value, window.location.origin);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return parsed.href;
    }
  } catch (error) {
    return "";
  }
  return "";
}

const listState = {
  query: "",
  weekendOnly: false,
  ready: false
};

function pageDefaultsToWeekend(pageName) {
  const params = new URLSearchParams(window.location.search);
  if (params.get("when") === "weekend") return true;
  if (params.get("when") === "any") return false;
  return pageName === "home";
}

function initListState(pageName) {
  if (listState.ready) return;
  const params = new URLSearchParams(window.location.search);
  listState.query = params.get("q") || "";
  listState.weekendOnly = pageDefaultsToWeekend(pageName);
  listState.ready = true;
}

function eventSearchText(event) {
  const display = getDisplayEvent(event);
  return [
    display.title,
    display.summary,
    display.location,
    display.venue,
    display.date,
    display.category,
    display.categoryLabel,
    ...safeArray(display.highlights),
    ...safeArray(display.description)
  ].join(" ").toLowerCase();
}

function applyListFilters(events) {
  const query = listState.query.trim().toLowerCase();
  return events.filter((event) => {
    if (listState.weekendOnly && !overlapsThisWeekend(event)) return false;
    if (!query) return true;
    return eventSearchText(event).includes(query);
  });
}

function emptyListingMessage(pageName) {
  if (listState.query) return t("common.noEvents");
  if (listState.weekendOnly) return t("common.noWeekendEvents");
  if (pageName === "film") return t("common.noConfirmedFilms");
  return t("common.noEvents");
}

function upsertMeta(attribute, key, content) {
  let element = document.head.querySelector(`meta[${attribute}="${key}"]`);
  if (!element) {
    element = document.createElement("meta");
    element.setAttribute(attribute, key);
    document.head.appendChild(element);
  }
  element.setAttribute("content", content);
}

function getEventDetailCopy(sourceEvent) {
  const display = getDisplayEvent(sourceEvent);
  const category = getCategoryKey(sourceEvent);
  const notice = availabilityMessage(sourceEvent);

  if (category === "film") {
    let dateLabel = display.date || t("common.datesNotListed");
    if (isUndatedNowShowingFilm(sourceEvent)) dateLabel = t("common.datesNotListed");
    if (isEnded(sourceEvent)) dateLabel = endedLabel(sourceEvent);
    return {
      location: "",
      locationVisible: false,
      date: `${t("common.statusLabel")}: ${dateLabel}`,
      dateVisible: true,
      access: "",
      accessVisible: safeArray(sourceEvent.screeningVenues).length > 0,
      aboutTitle: t("event.filmSynopsis"),
      availabilityMessage: notice
    };
  }

  return {
    location: display.location || "",
    locationVisible: Boolean(display.location),
    date: isEnded(sourceEvent) ? endedLabel(sourceEvent) : (display.date || ""),
    dateVisible: Boolean(display.date) || isEnded(sourceEvent),
    access: display.access || "-",
    accessVisible: Boolean(display.access),
    aboutTitle: t("event.aboutEvent"),
    availabilityMessage: notice
  };
}

function renderScreeningVenueLinks(event) {
  const venues = safeArray(event.screeningVenues);
  if (!venues.length) {
    return escapeHtml(event.access || "");
  }

  return venues
    .map((venue) => {
      const name = escapeHtml(venue.name || "");
      const url = safeUrl(venue.url);
      if (!name || !url) return "";
      return `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="text-red-500 hover:underline">${name}</a>`;
    })
    .filter(Boolean)
    .join('<span class="text-gray-400"> / </span>');
}

function getEventSlug(item) {
  return item?.slug || generateSlug(item?.title || "");
}

function getVisibleEvents(events) {
  return safeArray(events).filter(isListable);
}

function getCardMediaMarkup(item, options = {}) {
  const imageSrc = escapeHtml(item.image || getFallbackImage(item));
  const fallbackSrc = escapeHtml(getFallbackImage(item));
  const altText = escapeHtml(item.title || "");
  const extraClasses = options.extraClasses ? ` ${options.extraClasses}` : "";
  const sizeClasses = options.sizeClasses || "";
  const overlayClass =
    options.overlayClass ||
    "absolute inset-0 bg-gradient-to-t from-black/8 via-transparent to-transparent pointer-events-none";

  return `
    <div
      class="tw-card-media${extraClasses} ${sizeClasses}"
      style="--tw-card-image:url('${imageSrc}')"
    >
      <div class="tw-card-media__backdrop" aria-hidden="true"></div>
      <img
        src="${imageSrc}"
        alt="${altText}"
        class="w-full h-full"
        onerror="this.onerror=null;this.src='${fallbackSrc}';"
      >
      <div class="${overlayClass}"></div>
    </div>
  `;
}

function createCard(item) {
  const basePath = getBasePath();
  const itemSlug = getEventSlug(item);
  const category = getCategoryKey(item);

  const isLocalhost =
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "localhost";

  const detailUrl = isLocalhost
    ? `${basePath}event.html?slug=${encodeURIComponent(itemSlug)}`
    : `${basePath}event/${encodeURIComponent(itemSlug)}`;

  const mediaMarkup = getCardMediaMarkup(item, {
    extraClasses: category === "exhibition" ? " tw-card-media--exhibition" : "",
    sizeClasses: "aspect-[4/2.45]"
  });

  return `
  <a
    href="${detailUrl}"
    class="group block h-full"
  >
    <article class="h-full bg-white rounded-[24px] border border-gray-200/80 shadow-sm overflow-hidden transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg hover:border-gray-300">
      ${mediaMarkup}

      <div class="px-6 pt-5 pb-5 flex flex-col">
          <span class="tw-category-pill" data-category="${escapeHtml(category)}">
            ${escapeHtml(item.categoryLabel || item.category || "")}
          </span>

        <h3 class="mt-3 text-[18px] leading-[1.32] font-semibold text-gray-900 line-clamp-2">
          ${escapeHtml(item.title || "")}
        </h3>

        <p class="mt-2 text-gray-500 text-[13px] leading-[1.5] line-clamp-2">
          ${escapeHtml(getCardMeta(item))}
        </p>

        <span class="mt-4 inline-flex items-center text-[14px] text-red-500 transition-all duration-200 group-hover:translate-x-1">
          ${t("common.viewDetails")}
        </span>
      </div>
    </article>
  </a>
`;
}

function createTopPickCard(item) {
  const basePath = getBasePath();
  const itemSlug = getEventSlug(item);
  const category = getCategoryKey(item);

  const isLocalhost =
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "localhost";

  const detailUrl = isLocalhost
    ? `${basePath}event.html?slug=${encodeURIComponent(itemSlug)}`
    : `${basePath}event/${encodeURIComponent(itemSlug)}`;

  const mediaMarkup = getCardMediaMarkup(item, {
    extraClasses: ` tw-card-media--top-pick${category === "exhibition" ? " tw-card-media--exhibition" : ""}`,
    sizeClasses: "h-[190px]",
    overlayClass: "absolute inset-0 bg-gradient-to-t from-black/10 via-transparent to-transparent pointer-events-none"
  });

  return `
    <a href="${detailUrl}" class="block group h-full">
      <article class="h-full bg-white rounded-[22px] border border-gray-200 shadow-sm overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lg flex flex-col">
        ${mediaMarkup}

        <div class="p-4 flex flex-col flex-1">
            <span class="tw-category-pill" data-category="${escapeHtml(category)}">
              ${escapeHtml(item.categoryLabel || item.category || "")}
            </span>

          <h3 class="mt-3 text-[16px] leading-[1.4] font-semibold text-gray-900 min-h-[68px] line-clamp-3">
            ${escapeHtml(item.title || "")}
          </h3>

          <p class="mt-3 text-gray-500 text-[13px] leading-6 min-h-[72px] line-clamp-3">
            ${escapeHtml(getCardMeta(item))}
          </p>

          <span class="mt-auto pt-4 inline-block text-[14px] text-red-500 transition-all duration-200 group-hover:translate-x-1">
            ${t("common.viewDetails")}
          </span>
        </div>
      </article>
    </a>
  `;
}

function filterByCategory(events, pageName) {
  if (pageName === "film") {
    return events.filter((e) => e.category === "Film");
  }
  if (pageName === "exhibitions") {
    return events.filter((e) => e.category === "Exhibition");
  }
  if (pageName === "nightlife") {
    return events.filter((e) => e.category === "Nightlife");
  }
  if (pageName === "activities") {
    return events.filter((e) => e.category === "Activity");
  }
  return events;
}

function getFallbackImage(item) {
  return createSvgPlaceholder(item);
}

function applyStaticTranslations(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });

  root.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder));
  });

  root.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
  });
}

function applyPageLocalization() {
  const page = document.body.dataset.page || "home";

  if (page === "home") {
    document.title = t("meta.homeTitle");
  } else if (page === "film") {
    document.title = t("meta.filmTitle");
  } else if (page === "exhibitions") {
    document.title = t("meta.exhibitionsTitle");
  } else if (page === "nightlife") {
    document.title = t("meta.nightlifeTitle");
  } else if (page === "activities") {
    document.title = t("meta.activitiesTitle");
  } else if (page === "auth") {
    document.title = t("meta.authTitle");
  } else if (page === "account") {
    document.title = t("meta.accountTitle");
  } else if (page === "all") {
    document.title = t("meta.allTitle");
  } else if (page === "about") {
    document.title = t("meta.aboutTitle");
  } else if (page === "contact") {
    document.title = t("meta.contactTitle");
  }

  const highlightsTitle = document.querySelector("[data-event-heading='highlights']");
  if (highlightsTitle) highlightsTitle.textContent = t("event.highlights");

  const aboutTitle = document.getElementById("event-about-title");
  if (aboutTitle && !document.getElementById("event-title")) {
    aboutTitle.textContent = t("event.aboutEvent");
  }

}

function syncLanguageButtons() {
  const currentLanguage = getCurrentLanguage();
  document.querySelectorAll("[data-lang-switch]").forEach((button) => {
    const isActive = button.dataset.langSwitch === currentLanguage;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

function initLanguageSwitcher() {
  document.querySelectorAll("[data-lang-switch]").forEach((button) => {
    if (button.dataset.bound === "true") {
      return;
    }

    button.dataset.bound = "true";
    button.addEventListener("click", async () => {
      const nextLanguage = button.dataset.langSwitch || DEFAULT_LANGUAGE;
      setCurrentLanguage(nextLanguage);
      applyStaticTranslations();
      syncLanguageButtons();
      await rerenderCurrentView();
      document.dispatchEvent(new CustomEvent("tw:language-changed", { detail: { language: nextLanguage } }));
    });
  });
}

function listingPool(events, pageName) {
  const listable = getVisibleEvents(events);
  if (pageName === "home") {
    return listable.filter((event) => event.publishable !== false);
  }
  return filterByCategory(listable, pageName);
}

function ensureListingControls() {
  if (document.getElementById("event-search")) return;
  const container = document.getElementById("card-container");
  if (!container || !container.parentElement) return;

  const bar = document.createElement("div");
  bar.className = "flex flex-col sm:flex-row gap-3 mb-6";
  bar.innerHTML = `
    <input id="event-search" type="search" data-i18n-placeholder="home.searchPlaceholder" placeholder="${escapeHtml(t("home.searchPlaceholder"))}" class="border rounded-lg px-4 py-3 w-full bg-white" />
    <button id="weekend-filter" type="button" class="border border-gray-300 rounded-lg px-4 py-3 text-sm font-semibold bg-white shrink-0" data-i18n="common.thisWeekend">${escapeHtml(t("common.thisWeekend"))}</button>
  `;
  container.parentElement.insertBefore(bar, container);
}

function syncListControls() {
  const toggle = document.getElementById("weekend-filter");
  if (toggle) {
    toggle.setAttribute("aria-pressed", String(listState.weekendOnly));
    toggle.classList.toggle("is-active", listState.weekendOnly);
  }

  const input = document.getElementById("event-search");
  if (input && input.value !== listState.query) {
    input.value = listState.query;
  }

  const viewAll = document.getElementById("home-view-all");
  if (viewAll) {
    viewAll.href = listState.weekendOnly ? "/pages/all.html?when=weekend" : "/pages/all.html";
  }

  const heading = document.getElementById("home-results-title");
  if (heading) {
    heading.textContent = listState.query ? t("home.searchResults") : t("home.topPicksTitle");
  }
}

function bindListControls() {
  const input = document.getElementById("event-search");
  if (input && input.dataset.bound !== "true") {
    input.dataset.bound = "true";
    input.addEventListener("input", () => {
      listState.query = input.value;
      rerenderCurrentView();
    });
  }

  const toggle = document.getElementById("weekend-filter");
  if (toggle && toggle.dataset.bound !== "true") {
    toggle.dataset.bound = "true";
    toggle.addEventListener("click", () => {
      listState.weekendOnly = toggle.getAttribute("aria-pressed") !== "true";
      syncListControls();
      rerenderCurrentView();
    });
  }
}

async function renderCards(pageName) {
  const container = document.getElementById("card-container");
  if (!container) return;

  try {
    const events = await loadEvents();
    const items = applyListFilters(listingPool(events, pageName))
      .sort(compareRank)
      .map(getDisplayEvent);

    if (!items.length) {
      container.innerHTML = `<p class="text-gray-500 col-span-full">${escapeHtml(emptyListingMessage(pageName))}</p>`;
      return;
    }

    container.innerHTML = items.map(createCard).join("");
  } catch (error) {
    container.innerHTML = `<p class="text-red-500 col-span-full">${escapeHtml(t("common.loadEventsError"))}</p>`;
    console.error(error);
  }
}

async function renderTopPicks() {
  const container = document.getElementById("top-picks-container");
  if (!container) return;

  try {
    const events = await loadEvents();
    const filtered = applyListFilters(listingPool(events, "home")).sort(compareRank);
    const topPicks = (!listState.query && listState.weekendOnly ? filtered.slice(0, 4) : filtered)
      .map(getDisplayEvent);

    if (!topPicks.length) {
      container.innerHTML = `<p class="text-gray-500 col-span-full">${escapeHtml(emptyListingMessage("home"))}</p>`;
      return;
    }

    container.innerHTML = topPicks.map(createTopPickCard).join("");
  } catch (error) {
    container.innerHTML = `<p class="text-red-500 col-span-full">${escapeHtml(t("common.loadTopPicksError"))}</p>`;
    console.error(error);
  }
}

async function renderEventDetail() {
  const titleEl = document.getElementById("event-title");
  if (!titleEl) return;

  const params = new URLSearchParams(window.location.search);
  const querySlug = params.get("slug");

  const parts = window.location.pathname.split("/").filter(Boolean);
  let pathSlug = null;

  if (parts.length >= 2 && parts[0].toLowerCase() === "event") {
    pathSlug = parts[1].toLowerCase();
  }

  const slug = querySlug || pathSlug;
  const id = Number(params.get("id"));

  try {
    const events = await loadEvents();
    const normalizedSlug = slug ? decodeURIComponent(slug).toLowerCase() : "";

    const sourceEvent = normalizedSlug
      ? safeArray(events).find((e) => getEventSlug(e).toLowerCase() === normalizedSlug)
      : safeArray(events).find((e) => e.id === id);

    if (!sourceEvent) {
      titleEl.innerText = t("common.eventNotFound");
      return;
    }

    const event = getDisplayEvent(sourceEvent);
    const eventSlug = getEventSlug(sourceEvent);
    const descriptionList = safeArray(event.description);
    const highlightsList = safeArray(event.highlights);
    const descriptionText = descriptionList.join(" ").trim();

    document.title = `${event.title || t("meta.eventSuffix")} | ${t("meta.eventSuffix")}`;
    const shareUrl = `${window.location.origin}/event/${encodeURIComponent(eventSlug)}`;
    const metaDescription = event.summary || t("meta.homeTitle");
    upsertMeta("name", "description", metaDescription);
    upsertMeta("property", "og:title", document.title);
    upsertMeta("property", "og:description", metaDescription);
    upsertMeta("property", "og:url", shareUrl);
    if (event.image) {
      upsertMeta("property", "og:image", event.image);
    }

    let canonical = document.querySelector("link[rel='canonical']");
    if (!canonical) {
      canonical = document.createElement("link");
      canonical.rel = "canonical";
      document.head.appendChild(canonical);
    }
    canonical.href = shareUrl;

    let structuredData = document.getElementById("event-structured-data");
    if (!structuredData) {
      structuredData = document.createElement("script");
      structuredData.type = "application/ld+json";
      structuredData.id = "event-structured-data";
      document.head.appendChild(structuredData);
    }

    const schema = {
      "@context": "https://schema.org",
      "@type": "Event",
      name: event.title || "",
      description: descriptionText || "",
      image: event.image ? [event.image] : [],
      eventAttendanceMode: "https://schema.org/OfflineEventAttendanceMode",
      location: {
        "@type": "Place",
        name: event.location || "Tokyo"
      },
      organizer: {
        "@type": "Organization",
        name: event.source || t("meta.eventSuffix")
      },
      url: shareUrl
    };
    if (parseIsoDate(sourceEvent.startDate)) schema.startDate = sourceEvent.startDate;
    if (parseIsoDate(sourceEvent.endDate)) schema.endDate = sourceEvent.endDate;
    if (isListable(sourceEvent)) {
      schema.eventStatus = "https://schema.org/EventScheduled";
    }
    structuredData.text = JSON.stringify(schema);

    const categoryEl = document.getElementById("event-category");
    if (categoryEl) {
      categoryEl.innerText = event.categoryLabel || event.category || "";
      categoryEl.dataset.category = getCategoryKey(sourceEvent);
    }

    titleEl.innerText = event.title || "";
    const detailCopy = getEventDetailCopy(sourceEvent);
    const banner = document.getElementById("event-status-banner");
    if (banner) {
      banner.hidden = !detailCopy.availabilityMessage;
      banner.textContent = detailCopy.availabilityMessage || "";
    }

    const locationRow = document.getElementById("event-location-row");
    const locationEl = document.getElementById("event-location");
    if (locationEl) {
      locationEl.innerText = detailCopy.location;
    }
    if (locationRow) {
      locationRow.style.display = detailCopy.locationVisible ? "flex" : "none";
    }

    const dateRow = document.getElementById("event-date-row");
    const dateEl = document.getElementById("event-date");
    if (dateEl) {
      dateEl.innerText = detailCopy.date;
    }
    if (dateRow) {
      dateRow.style.display = detailCopy.dateVisible ? "flex" : "none";
    }

    const accessRow = document.getElementById("event-access-row");
    const accessEl = document.getElementById("event-access");
    if (accessEl) {
      if (getCategoryKey(sourceEvent) === "film") {
        accessEl.innerHTML = renderScreeningVenueLinks(sourceEvent);
      } else {
        accessEl.innerText = detailCopy.access;
      }
    }
    if (accessRow) {
      accessRow.style.display = detailCopy.accessVisible ? "flex" : "none";
    }

    const aboutTitleEl = document.getElementById("event-about-title");
    if (aboutTitleEl) {
      aboutTitleEl.innerText = detailCopy.aboutTitle;
    }

    const imageEl = document.getElementById("event-image");
    if (imageEl) {
      imageEl.src = event.image || getFallbackImage(event);
      imageEl.alt = event.title || "";

      imageEl.onerror = function () {
        this.onerror = null;
        this.src = getFallbackImage(event);
      };
    }

    const summaryEl = document.getElementById("event-summary");
    if (summaryEl) {
      summaryEl.innerText = event.summary || "";
      summaryEl.style.display = event.summary ? "block" : "none";
    }

    const descriptionEl = document.getElementById("event-description");
    if (descriptionEl) {
      if (descriptionList.length > 0) {
        descriptionEl.innerHTML = descriptionList
          .map((paragraph) => `<p class="mb-4">${escapeHtml(paragraph)}</p>`)
          .join("");
      } else {
        descriptionEl.innerText = event.description || "";
      }
    }

    const highlightsEl = document.getElementById("event-highlights");
    const highlightsSection = highlightsEl?.closest(".rounded-3xl");
    if (highlightsEl) {
      if (highlightsList.length === 0) {
        highlightsEl.innerHTML = "";
        if (highlightsSection) {
          highlightsSection.style.display = "none";
        }
      } else {
        if (highlightsSection) {
          highlightsSection.style.display = "block";
        }
        highlightsEl.innerHTML = "";
        highlightsList.forEach((text) => {
          const li = document.createElement("li");
          li.className = "flex items-start gap-3 text-[15px] leading-[1.42] text-gray-800";
          li.innerHTML = `
            <span class="w-2 h-2 bg-red-500 rounded-full mt-[7px] shrink-0"></span>
            <span>${escapeHtml(text)}</span>
          `;
          highlightsEl.appendChild(li);
        });
      }
    }

    const sourceEl = document.getElementById("event-source");
    if (sourceEl) {
      sourceEl.innerText = event.source || t("common.unknownSource");
    }

    const sourceLink = document.getElementById("event-source-link");
    if (sourceLink) {
      sourceLink.textContent = t("common.visitSource");
      const sourceHref = safeUrl(sourceEvent.sourceUrl);
      if (sourceHref) {
        sourceLink.href = sourceHref;
        sourceLink.style.display = "inline-block";
      } else {
        sourceLink.style.display = "none";
      }
    }

    applyPageLocalization();
  } catch (error) {
    titleEl.innerText = t("common.eventLoadError");
    console.error(error);
  }
}

async function loadHeader() {
  try {
    const res = await fetch("/components/header.html");
    if (!res.ok) {
      throw new Error("Failed to load header component");
    }

    const html = await res.text();
    const headerEl = document.getElementById("header");

    if (headerEl) {
      headerEl.innerHTML = html;
    }

    initMenu();
    initLanguageSwitcher();
    applyStaticTranslations(headerEl || document);
    syncLanguageButtons();
    if (window.TWAuth && typeof window.TWAuth.renderHeaderAuth === "function") {
      await window.TWAuth.renderHeaderAuth();
    }
  } catch (error) {
    console.error(error);
  }
}

function initMenu() {
  const openMenuBtn = document.getElementById("open-menu");
  const closeMenuBtn = document.getElementById("close-menu");
  const sideMenu = document.getElementById("side-menu");
  const menuOverlay = document.getElementById("menu-overlay");

  if (!openMenuBtn || !closeMenuBtn || !sideMenu || !menuOverlay) {
    return;
  }

  function openMenu() {
    sideMenu.classList.remove("-translate-x-full");
    sideMenu.classList.add("translate-x-0");

    menuOverlay.classList.remove("opacity-0", "pointer-events-none");
    menuOverlay.classList.add("opacity-100");

    document.body.classList.add("overflow-hidden");
  }

  function closeMenu() {
    sideMenu.classList.remove("translate-x-0");
    sideMenu.classList.add("-translate-x-full");

    menuOverlay.classList.remove("opacity-100");
    menuOverlay.classList.add("opacity-0", "pointer-events-none");

    document.body.classList.remove("overflow-hidden");
  }

  openMenuBtn.addEventListener("click", openMenu);
  closeMenuBtn.addEventListener("click", closeMenu);
  menuOverlay.addEventListener("click", closeMenu);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeMenu();
    }
  });
}

async function rerenderCurrentView() {
  applyStaticTranslations();
  applyPageLocalization();
  syncListControls();

  const page = document.body.dataset.page || "home";

  if (page === "event") {
    await renderEventDetail();
    return;
  }

  if (page === "home") {
    await renderTopPicks();
    return;
  }

  if (page === "auth") {
    return;
  }

  if (page === "account") {
    return;
  }

  await renderCards(page);
}

async function initializePage(pageName) {
  const currentPage = pageName || document.body.dataset.page || "home";
  document.body.dataset.page = currentPage;
  setCurrentLanguage(getCurrentLanguage());
  initListState(currentPage);
  ensureListingControls();
  bindListControls();
  applyStaticTranslations();
  syncListControls();
  await loadHeader();
  await rerenderCurrentView();
}

window.t = t;
window.initializePage = initializePage;
