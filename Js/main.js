async function loadEvents() {
  const res = await fetch(getEventsJsonPath());
  if (!res.ok) {
    throw new Error("Failed to load events.json");
  }
  return await res.json();
}

function getEventsJsonPath() {
  return "/data/generated_events.json";
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

function getEventSlug(item) {
  return item?.slug || generateSlug(item?.title || "");
}

function getVisibleEvents(events) {
  return safeArray(events);
}

function createCard(item) {
  const basePath = getBasePath();
  const itemSlug = getEventSlug(item);

  const isLocalhost =
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "localhost";

  const detailUrl = isLocalhost
    ? `${basePath}event.html?slug=${itemSlug}`
    : `${basePath}event/${itemSlug}`;

  return `
    <a
      href="${detailUrl}"
      class="group block h-full"
    >
      <article class="h-full bg-white rounded-[24px] border border-gray-200/80 shadow-sm overflow-hidden transition-all duration-300 ease-out hover:-translate-y-1.5 hover:shadow-xl hover:border-gray-300">
        
        <div class="relative aspect-[4/2.5] overflow-hidden bg-gray-100">
          <img
            src="${item.image || getFallbackImage(item)}"
            alt="${item.title || ""}"
            class="w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.03]"
            onerror="this.onerror=null;this.src='${getFallbackImage(item)}';"
          >
          <div class="absolute inset-0 bg-gradient-to-t from-black/8 via-transparent to-transparent pointer-events-none"></div>
        </div>

        <div class="p-5 md:p-6 flex flex-col min-h-[168px]">
          <span class="text-[11px] text-red-500 font-semibold uppercase tracking-[0.14em]">
            ${item.category || ""}
          </span>

          <h3 class="mt-3 text-[18px] leading-[1.35] font-semibold text-gray-900 line-clamp-2">
            ${item.title || ""}
          </h3>

          <p class="mt-3 text-gray-500 text-[13px] leading-[1.55] line-clamp-2">
            ${(item.location || "").trim()}${item.date ? ` • ${item.date}` : ""}
          </p>

          <span class="mt-auto pt-5 inline-flex items-center text-[14px] text-red-500 transition-all duration-200 group-hover:translate-x-1 group-hover:text-red-400">
            View details →
          </span>
        </div>
      </article>
    </a>
  `;
}

function createTopPickCard(item) {
  const basePath = getBasePath();
  const itemSlug = getEventSlug(item);

  const isLocalhost =
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "localhost";

  const detailUrl = isLocalhost
    ? `${basePath}event.html?slug=${itemSlug}`
    : `${basePath}event/${itemSlug}`;

  return `
    <a href="${detailUrl}" class="block group h-full">
      <article class="h-full bg-white rounded-[22px] border border-gray-200 shadow-sm overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lg flex flex-col">
        <div class="overflow-hidden">
          <img
            src="${item.image || getFallbackImage(item)}"
            alt="${item.title || ""}"
            class="w-full h-[190px] object-cover transition-transform duration-500 group-hover:scale-105"
            onerror="this.onerror=null;this.src='${getFallbackImage(item)}';"
          >
        </div>

        <div class="p-4 flex flex-col flex-1">
          <span class="text-[11px] text-red-500 font-semibold uppercase tracking-[0.12em]">
            ${item.category || ""}
          </span>

          <h3 class="mt-3 text-[16px] leading-[1.4] font-semibold text-gray-900 min-h-[68px] line-clamp-3">
            ${item.title || ""}
          </h3>

          <p class="mt-3 text-gray-500 text-[13px] leading-6 min-h-[72px] line-clamp-3">
            ${(item.location || "").trim()}${item.date ? ` • ${item.date}` : ""}
          </p>

          <span class="mt-auto pt-4 inline-block text-[14px] text-red-500 transition-all duration-200 group-hover:translate-x-1">
            View details →
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
  const category = (item.category || "").toLowerCase();

  if (category === "nightlife") {
    return "/images/fallback/nightlife.png";
  }

  if (category === "film") {
    return "/images/fallback/film.png";
  }

  if (category === "activity") {
    return "/images/fallback/activity.png";
  }

  return "/images/fallback/mot-logo.png";
}

async function renderCards(pageName) {
  const container = document.getElementById("card-container");
  if (!container) return;

  try {
    const events = await loadEvents();
    const visibleEvents = getVisibleEvents(events);
    const items = filterByCategory(visibleEvents, pageName);

    if (!items.length) {
      container.innerHTML = `<p class="text-gray-500">No events found.</p>`;
      return;
    }

    container.innerHTML = items.map(createCard).join("");
  } catch (error) {
    container.innerHTML = `<p class="text-red-500">Failed to load events.</p>`;
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
      .slice(0, 4);

    if (!topPicks.length) {
      container.innerHTML = `<p class="text-gray-500">No top picks available.</p>`;
      return;
    }

    container.innerHTML = topPicks.map(createTopPickCard).join("");
  } catch (error) {
    container.innerHTML = `<p class="text-red-500">Failed to load top picks.</p>`;
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

    const event = slug
      ? visibleEvents.find((e) => getEventSlug(e) === slug)
      : visibleEvents.find((e) => e.id === id);

    if (!event) {
      titleEl.innerText = "Event not found";
      return;
    }

    const eventSlug = getEventSlug(event);
    const descriptionList = safeArray(event.description);
    const highlightsList = safeArray(event.highlights);

    const descriptionText =
      descriptionList.length > 0
        ? descriptionList.join(" ")
        : (event.description || "");

    document.title = `${event.title || "Event"} | Tokyo Weekend`;

    let meta = document.querySelector('meta[name="description"]');
    if (!meta) {
      meta = document.createElement("meta");
      meta.name = "description";
      document.head.appendChild(meta);
    }
    meta.content = descriptionText || `${event.title || "Event"} in Tokyo.`;

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
        name: event.source || "Tokyo Weekend"
      },
      url: `${window.location.origin}/event/${eventSlug}`
    });

    const categoryEl = document.getElementById("event-category");
    if (categoryEl) {
      categoryEl.innerText = event.category || "";
    }

    titleEl.innerText = event.title || "";

    const locationEl = document.getElementById("event-location");
    if (locationEl) {
      locationEl.innerText = event.location || "";
    }

    const dateEl = document.getElementById("event-date");
    if (dateEl) {
      dateEl.innerText = event.date || "";
    }

    const accessEl = document.getElementById("event-access");
    if (accessEl) {
      accessEl.innerText = event.access || "-";
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
          .map((p) => `<p class="mb-4">${p}</p>`)
          .join("");
      } else {
        descriptionEl.innerText = event.description || "";
      }
    }

    const highlightsEl = document.getElementById("event-highlights");
    if (highlightsEl) {
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

    const sourceEl = document.getElementById("event-source");
    if (sourceEl) {
      sourceEl.innerText = event.source || "Unknown";
    }

    const sourceLink = document.getElementById("event-source-link");
    if (sourceLink) {
      if (event.sourceUrl) {
        sourceLink.href = event.sourceUrl;
        sourceLink.style.display = "inline-block";
      } else {
        sourceLink.style.display = "none";
      }
    }
  } catch (error) {
    titleEl.innerText = "Failed to load event";
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

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeMenu();
    }
  });
}

// Page entry
const path = window.location.pathname;

if (path.includes("event.html") || path.startsWith("/event/")) {
  renderEventDetail();
} else {
  renderTopPicks();
}