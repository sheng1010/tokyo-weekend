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
      follow: "Follow",
      about: "About",
      contact: "Contact",
      footer: "Tokyo Weekend Guide © 2026",
      viewAll: "View all",
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
      topPicksTitle: "Top Picks This Weekend"
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
      topPicksTitle: "今週末の注目イベント"
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
      topPicksTitle: "本周末精选"
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
    return t("common.nowShowing");
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
      label: "NOW SHOWING"
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

function getEventDetailCopy(event) {
  const category = getCategoryKey(event);

  if (category === "film") {
    return {
      location: "",
      locationVisible: false,
      date: event.date ? `${t("common.statusLabel")}: ${event.date}` : `${t("common.statusLabel")}: ${t("common.nowShowing")}`,
      dateVisible: true,
      access: "",
      accessVisible: safeArray(event.screeningVenues).length > 0,
      aboutTitle: t("event.filmSynopsis"),
      ratingVisible: false
    };
  }

  return {
    location: event.location || "",
    locationVisible: Boolean(event.location),
    date: event.date || "",
    dateVisible: Boolean(event.date),
    access: event.access || "-",
    accessVisible: Boolean(event.access),
    aboutTitle: t("event.aboutEvent"),
    ratingVisible: true
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
      const url = escapeHtml(venue.url || "#");
      return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-red-500 hover:underline">${name}</a>`;
    })
    .join('<span class="text-gray-400"> / </span>');
}

function getEventSlug(item) {
  return item?.slug || generateSlug(item?.title || "");
}

function getVisibleEvents(events) {
  return safeArray(events).filter(hasRealImage);
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
    ? `${basePath}event.html?slug=${itemSlug}`
    : `${basePath}event/${itemSlug}`;

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
          <span class="tw-category-pill" data-category="${category}">
            ${item.categoryLabel || item.category || ""}
          </span>

        <h3 class="mt-3 text-[18px] leading-[1.32] font-semibold text-gray-900 line-clamp-2">
          ${item.title || ""}
        </h3>

        <p class="mt-2 text-gray-500 text-[13px] leading-[1.5] line-clamp-2">
          ${getCardMeta(item)}
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
    ? `${basePath}event.html?slug=${itemSlug}`
    : `${basePath}event/${itemSlug}`;

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
            <span class="tw-category-pill" data-category="${category}">
              ${item.categoryLabel || item.category || ""}
            </span>

          <h3 class="mt-3 text-[16px] leading-[1.4] font-semibold text-gray-900 min-h-[68px] line-clamp-3">
            ${item.title || ""}
          </h3>

          <p class="mt-3 text-gray-500 text-[13px] leading-6 min-h-[72px] line-clamp-3">
            ${getCardMeta(item)}
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
  }

  const highlightsTitle = document.querySelector("[data-event-heading='highlights']");
  if (highlightsTitle) highlightsTitle.textContent = t("event.highlights");

  const ratingTitle = document.querySelector("[data-event-heading='rating']");
  if (ratingTitle) ratingTitle.textContent = t("event.visitorRating");

  const aboutTitle = document.getElementById("event-about-title");
  if (aboutTitle && !document.getElementById("event-title")) {
    aboutTitle.textContent = t("event.aboutEvent");
  }

  const outOfFive = document.querySelector("[data-i18n-static='outOfFive']");
  if (outOfFive) outOfFive.textContent = t("common.outOfFive");

  const basedOnReviews = document.getElementById("event-rating-count");
  if (basedOnReviews) basedOnReviews.textContent = t("common.basedOnReviews");
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
    });
  });
}

async function renderCards(pageName) {
  const container = document.getElementById("card-container");
  if (!container) return;

  try {
    const events = await loadEvents();
    const visibleEvents = getVisibleEvents(events);
    const items = filterByCategory(visibleEvents, pageName).map(getDisplayEvent);

    if (!items.length) {
      container.innerHTML = `<p class="text-gray-500">${t("common.noEvents")}</p>`;
      return;
    }

    container.innerHTML = items.map(createCard).join("");
  } catch (error) {
    container.innerHTML = `<p class="text-red-500">${t("common.loadEventsError")}</p>`;
    console.error(error);
  }
}

async function renderTopPicks() {
  const container = document.getElementById("top-picks-container");
  if (!container) return;

  try {
    const events = await loadEvents();
    const visibleEvents = getVisibleEvents(events);
    const topPicks = visibleEvents
      .slice()
      .sort((a, b) => (b.qualityScore || 0) - (a.qualityScore || 0))
      .slice(0, 4)
      .map(getDisplayEvent);

    if (!topPicks.length) {
      container.innerHTML = `<p class="text-gray-500">${t("common.noTopPicks")}</p>`;
      return;
    }

    container.innerHTML = topPicks.map(createTopPickCard).join("");
  } catch (error) {
    container.innerHTML = `<p class="text-red-500">${t("common.loadTopPicksError")}</p>`;
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
    const visibleEvents = getVisibleEvents(events);

    const sourceEvent = slug
      ? visibleEvents.find((e) => getEventSlug(e) === slug)
      : visibleEvents.find((e) => e.id === id);

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

    let canonical = document.querySelector("link[rel='canonical']");
    if (!canonical) {
      canonical = document.createElement("link");
      canonical.rel = "canonical";
      document.head.appendChild(canonical);
    }
    canonical.href = `${window.location.origin}/event/${eventSlug}`;

    let structuredData = document.getElementById("event-structured-data");
    if (!structuredData) {
      structuredData = document.createElement("script");
      structuredData.type = "application/ld+json";
      structuredData.id = "event-structured-data";
      document.head.appendChild(structuredData);
    }

    structuredData.text = JSON.stringify({
      "@context": "https://schema.org",
      "@type": "Event",
      name: event.title || "",
      description: descriptionText || "",
      image: event.image ? [event.image] : [],
      eventAttendanceMode: "https://schema.org/OfflineEventAttendanceMode",
      eventStatus: "https://schema.org/EventScheduled",
      location: {
        "@type": "Place",
        name: event.location || "Tokyo"
      },
      organizer: {
        "@type": "Organization",
        name: event.source || t("meta.eventSuffix")
      },
      url: `${window.location.origin}/event/${eventSlug}`
    });

    const categoryEl = document.getElementById("event-category");
    if (categoryEl) {
      categoryEl.innerText = event.categoryLabel || event.category || "";
      categoryEl.dataset.category = getCategoryKey(sourceEvent);
    }

    titleEl.innerText = event.title || "";
    const detailCopy = getEventDetailCopy(event);

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

    const ratingSection = document.getElementById("event-rating-section");
    if (ratingSection) {
      ratingSection.style.display = detailCopy.ratingVisible ? "block" : "none";
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
          .map((paragraph) => `<p class="mb-4">${paragraph}</p>`)
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
            <span>${text}</span>
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
      if (sourceEvent.sourceUrl) {
        sourceLink.href = sourceEvent.sourceUrl;
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

  const page = document.body.dataset.page || "home";

  if (page === "event") {
    await renderEventDetail();
    return;
  }

  if (page === "home") {
    await renderTopPicks();
    return;
  }

  await renderCards(page);
}

async function initializePage(pageName) {
  const currentPage = pageName || document.body.dataset.page || "home";
  document.body.dataset.page = currentPage;
  setCurrentLanguage(getCurrentLanguage());
  applyStaticTranslations();
  await loadHeader();
  await rerenderCurrentView();
}
