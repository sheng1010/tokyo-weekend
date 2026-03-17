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

function createCard(item) {
  const basePath = getBasePath();

  return `
    <div class="group bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden transition-all duration-300 ease-out hover:-translate-y-1.5 hover:shadow-xl hover:border-gray-300">
      <div class="overflow-hidden">
        <img
          src="${item.image}"
          alt="${item.title}"
          class="w-full h-48 object-cover transition-transform duration-500 ease-out group-hover:scale-105"
        >
      </div>

      <div class="p-5">
        <span class="text-xs text-red-500 font-semibold uppercase tracking-wide">
          ${item.category}
        </span>

        <h3 class="font-semibold text-lg leading-snug mt-3 text-gray-900">
          ${item.title}
        </h3>

        <p class="text-gray-500 text-sm mt-3 leading-6">
          ${item.location} • ${item.date}
        </p>

        <a
          href="${basePath}event/${generateSlug(item.title)}"
          class="mt-5 inline-block text-sm text-red-500 transition-all duration-200 group-hover:translate-x-1 group-hover:text-red-400"
        >
          View details →
        </a>
      </div>
    </div>
  `;
}

function filterByCategory(events, pageName) {
  if (pageName === "film") return events.filter(e => e.category === "Film");
  if (pageName === "exhibitions") return events.filter(e => e.category === "Exhibition");
  if (pageName === "nightlife") return events.filter(e => e.category === "Nightlife");
  if (pageName === "events") return events.filter(e => e.category === "Event");
  return events;
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

  const path = window.location.pathname.toLowerCase();
  const pathSlug = path.startsWith("/event/") ? path.slice("/event/".length) : null;

  const slug = querySlug || pathSlug;
  const id = Number(params.get("id"));

  try {
    const events = await loadEvents();

    const event = slug
      ? events.find(e => generateSlug(e.title) === slug)
      : events.find(e => e.id === id);

    if (!event) {
      titleEl.innerText = "Event not found";
      return;
    }

    document.title = `${event.title} | Tokyo Weekend`;

    let meta = document.querySelector('meta[name="description"]');
    if (!meta) {
      meta = document.createElement("meta");
      meta.name = "description";
      document.head.appendChild(meta);
    }
    meta.content = event.description || `${event.title} in Tokyo.`;

    // canonical
    let canonical = document.querySelector("link[rel='canonical']");
    if (!canonical) {
      canonical = document.createElement("link");
      canonical.rel = "canonical";
      document.head.appendChild(canonical);
    }
    canonical.href = `${window.location.origin}/event/${generateSlug(event.title)}`;

    // structured data
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
      "name": event.title || "",
      "description": event.description || "",
      "image": event.image ? [event.image] : [],
      "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
      "eventStatus": "https://schema.org/EventScheduled",
      "location": {
        "@type": "Place",
        "name": event.location || "Tokyo"
      },
      "organizer": {
        "@type": "Organization",
        "name": event.source || "Tokyo Weekend"
      },
      "url": `${window.location.origin}/event/${generateSlug(event.title)}`
    });

    document.getElementById("event-title").innerText = event.title || "";
    document.getElementById("event-category").innerText = event.category || "";
    document.getElementById("event-location").innerText = event.location || "";
    document.getElementById("event-date").innerText = event.date || "";

    const imageEl = document.getElementById("event-image");
    if (imageEl) {
      imageEl.src = event.image || "";
      imageEl.alt = event.title || "";
    }

    document.getElementById("event-description").innerText = event.description || "";

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