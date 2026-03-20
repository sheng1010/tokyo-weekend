async function loadEvents() {
  const res = await fetch(getEventsJsonPath());
  if (!res.ok) {
    throw new Error("Failed to load events.json");
  }
  return await res.json();
}

function getEventsJsonPath() {
  return "/data/events.json";
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
    <div class="group bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden transition-all duration-300 ease-out hover:-translate-y-1.5 hover:shadow-xl hover:border-gray-300">
      <div class="overflow-hidden">
        <img
          src="${item.image || getFallbackImage(item)}"
          alt="${item.title || ""}"
          class="w-full h-48 object-cover transition-transform duration-500 ease-out group-hover:scale-105"
          onerror="this.onerror=null;this.src='${getFallbackImage(item)}';"
        >
      </div>

      <div class="p-5">
        <span class="text-xs text-red-500 font-semibold uppercase tracking-wide">
          ${item.category || ""}
        </span>

        <h3 class="font-semibold text-lg leading-snug mt-3 text-gray-900">
          ${item.title || ""}
        </h3>

        <p class="text-gray-500 text-sm mt-3 leading-6">
          ${(item.location || "").trim()}${item.date ? ` • ${item.date}` : ""}
        </p>

        <a
          href="${detailUrl}"
          class="mt-5 inline-block text-sm text-red-500 transition-all duration-200 group-hover:translate-x-1 group-hover:text-red-400"
        >
          View details →
        </a>
      </div>
    </div>
  `;
}

function filterByCategory(events, pageName) {
  if (pageName === "film") return events.filter((e) => e.category === "Film");
  if (pageName === "exhibitions") return events.filter((e) => e.category === "Exhibition");
  if (pageName === "nightlife") return events.filter((e) => e.category === "Nightlife");
  if (pageName === "events") return events.filter((e) => e.category === "Event");
  return events;
}

function getFallbackImage(item) {
  const text = `${item.location || ""} ${item.source || ""}`.toLowerCase();

  if (text.includes("museum of contemporary art tokyo") || text.includes("mot")) {
    return "/images/fallback/mot-logo.png";
  }

  if (text.includes("mori art museum") || text.includes("mori")) {
    return "/images/fallback/mori-logo.png";
  }

  if (text.includes("national art center") || text.includes("nact")) {
    return "/images/fallback/nact-logo.png";
  }

  return "/images/fallback/default-museum.png";
}

async function renderCards(pageName) {
  const container = document.getElementById("card-container");
  if (!container) return;

  try {
    const events = await loadEvents();
    const items = filterByCategory(events, pageName);
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
    const topPicks = events.slice(0, 4);
    container.innerHTML = topPicks.map(createCard).join("");
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

    const event = slug
      ? events.find((e) => getEventSlug(e) === slug)
      : events.find((e) => e.id === id);

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
      if (highlightsList.length > 0) {
        highlightsEl.innerHTML = highlightsList
          .map(
            (item) => `
            <li class="flex items-start gap-3">
              <span class="mt-[8px] w-2.5 h-2.5 bg-red-500 rounded-full shrink-0"></span>
              <span class="text-[15px] md:text-lg leading-[1.75] text-gray-800">
                ${item}
              </span>
            </li>
          `
          )
          .join("");
      } else if (highlightsEl.parentElement) {
        highlightsEl.parentElement.style.display = "none";
      }
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
const isDetailPage = window.location.pathname.includes("event.html");
if (isDetailPage) {
  renderEventDetail();
}