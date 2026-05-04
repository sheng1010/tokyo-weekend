const calendarState = {
  viewDate: startOfMonth(new Date()),
  selectedDate: stripTime(new Date())
};

const sampleActivitiesByDate = {
  "2026-05-09": [
    {
      title: "Late screening shortlist",
      category: "Film",
      detail: "Hold space for one evening screening near Yurakucho."
    }
  ],
  "2026-05-16": [
    {
      title: "Museum afternoon",
      category: "Exhibition",
      detail: "Pair one major exhibition with a slower lunch nearby."
    },
    {
      title: "Night plan placeholder",
      category: "Nightlife",
      detail: "Reserve this slot for a later venue decision."
    }
  ],
  "2026-05-23": [
    {
      title: "Outdoor activity block",
      category: "Activity",
      detail: "Keep the afternoon open for a seasonal event or walk."
    }
  ]
};

const planTemplate = [
  { slot: "Morning", detail: "No plan yet" },
  { slot: "Afternoon", detail: "No plan yet" },
  { slot: "Evening", detail: "No plan yet" }
];

let initialized = false;

function stripTime(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function startOfMonth(date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function addMonths(date, delta) {
  return new Date(date.getFullYear(), date.getMonth() + delta, 1);
}

function pad(value) {
  return String(value).padStart(2, "0");
}

function getDateKey(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function isSameDay(a, b) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function getLocale() {
  const lang = (document.documentElement.lang || "en").toLowerCase();
  if (lang.startsWith("ja")) return "ja-JP";
  if (lang.startsWith("zh")) return "zh-CN";
  return "en-US";
}

function formatMonth(date) {
  return new Intl.DateTimeFormat(getLocale(), {
    month: "long",
    year: "numeric"
  }).format(date);
}

function formatFullDate(date) {
  return new Intl.DateTimeFormat(getLocale(), {
    weekday: "long",
    month: "long",
    day: "numeric"
  }).format(date);
}

function getWeekdayLabels() {
  const base = new Date(Date.UTC(2024, 0, 1));
  return Array.from({ length: 7 }, (_, index) => {
    const day = new Date(base);
    day.setUTCDate(base.getUTCDate() + index);
    return new Intl.DateTimeFormat(getLocale(), { weekday: "short" }).format(day);
  });
}

function t(key, fallback, replacements = {}) {
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

function getAuthState() {
  if (window.TWAuth && typeof window.TWAuth.getState === "function") {
    return window.TWAuth.getState();
  }
  return { user: null };
}

function buildSignInHref() {
  if (window.TWAuth && typeof window.TWAuth.buildAuthHref === "function") {
    return window.TWAuth.buildAuthHref(
      "signin",
      `${window.location.pathname}${window.location.search}${window.location.hash}`
    );
  }
  return "/pages/auth.html";
}

function getActivitiesForDate(date) {
  return sampleActivitiesByDate[getDateKey(date)] || [];
}

function getScheduleForDate(date) {
  const entries = getActivitiesForDate(date);
  const schedule = planTemplate.map((item) => ({
    slot: t(`accountHome.schedule${item.slot}`, item.slot),
    detail: t("accountHome.scheduleEmpty", item.detail)
  }));

  if (entries[0]) {
    schedule[1].detail = entries[0].title;
  }
  if (entries[1]) {
    schedule[2].detail = entries[1].title;
  }

  return schedule;
}

function renderAuthStatusCard() {
  const container = document.getElementById("account-auth-status");
  if (!container) {
    return;
  }

  const authState = getAuthState();
  if (authState.user) {
    const name = authState.user.displayName || authState.user.email?.split("@")[0] || "Member";
    const email = authState.user.email || "";

    container.innerHTML = `
      <p class="tw-account-home__status-label">${t("accountHome.linkingReady", "Activity linking ready")}</p>
      <h2 class="tw-account-home__status-title">${name}</h2>
      <p class="tw-account-home__status-copy">${email}</p>
      <p class="tw-account-home__status-note">${t("accountHome.linkingReadyBody", "This page is prepared for attaching saved events, screenings, and exhibitions to specific dates later on.")}</p>
    `;
    return;
  }

  container.innerHTML = `
    <p class="tw-account-home__status-label">${t("accountHome.guestTitle", "Sign in for personal planning")}</p>
    <p class="tw-account-home__status-note">${t("accountHome.guestBody", "Your calendar is visible now, but sign in before you start saving activity links and notes.")}</p>
    <a class="tw-account-home__status-action" href="${buildSignInHref()}">
      ${t("accountHome.signInAction", "Sign in to continue")}
    </a>
  `;
}

function renderWeekdays() {
  const container = document.getElementById("account-calendar-weekdays");
  if (!container) {
    return;
  }

  container.innerHTML = getWeekdayLabels()
    .map((label) => `<span>${label}</span>`)
    .join("");
}

function buildCalendarDays() {
  const firstDay = startOfMonth(calendarState.viewDate);
  const startOffset = (firstDay.getDay() + 6) % 7;
  const gridStart = new Date(firstDay);
  gridStart.setDate(firstDay.getDate() - startOffset);

  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(gridStart);
    date.setDate(gridStart.getDate() + index);
    return date;
  });
}

function renderCalendar() {
  const monthLabel = document.getElementById("account-calendar-month");
  const grid = document.getElementById("account-calendar-grid");
  if (!monthLabel || !grid) {
    return;
  }

  monthLabel.textContent = formatMonth(calendarState.viewDate);

  const today = stripTime(new Date());
  grid.innerHTML = buildCalendarDays()
    .map((date) => {
      const activities = getActivitiesForDate(date);
      const isCurrentMonth = date.getMonth() === calendarState.viewDate.getMonth();
      const isSelected = isSameDay(date, calendarState.selectedDate);
      const isToday = isSameDay(date, today);
      const countLabel =
        activities.length === 1
          ? t("accountHome.markerSingle", "1 plan")
          : t("accountHome.markerPlural", "{count} plans", { count: activities.length });

      return `
        <button
          type="button"
          class="tw-calendar-day${isCurrentMonth ? "" : " is-muted"}${isSelected ? " is-selected" : ""}${isToday ? " is-today" : ""}"
          data-calendar-date="${getDateKey(date)}"
        >
          <span class="tw-calendar-day__number">${date.getDate()}</span>
          <span class="tw-calendar-day__meta">
            ${activities.length ? `<span class="tw-calendar-day__count">${countLabel}</span>` : `<span class="tw-calendar-day__empty">&nbsp;</span>`}
          </span>
        </button>
      `;
    })
    .join("");
}

function renderSelectedDay() {
  const title = document.getElementById("account-selected-day");
  const summary = document.getElementById("account-selected-summary");
  const count = document.getElementById("account-selected-count");
  const list = document.getElementById("account-linked-activities");
  const plan = document.getElementById("account-day-plan");

  if (!title || !summary || !count || !list || !plan) {
    return;
  }

  const activities = getActivitiesForDate(calendarState.selectedDate);
  title.textContent = formatFullDate(calendarState.selectedDate);
  count.textContent = String(activities.length);
  summary.textContent = activities.length
    ? `${activities.length} ${activities.length === 1 ? "activity idea is" : "activity ideas are"} reserved for this date.`
    : t("accountHome.noActivitiesBody", "Once activity linking is enabled, your saved Tokyo Weekend picks will appear here for the selected day.");

  if (!activities.length) {
    list.innerHTML = `
      <div class="tw-linked-activities__empty">
        <strong>${t("accountHome.noActivities", "No linked activities yet.")}</strong>
        <p>${t("accountHome.noActivitiesBody", "Once activity linking is enabled, your saved Tokyo Weekend picks will appear here for the selected day.")}</p>
      </div>
    `;
  } else {
    list.innerHTML = activities
      .map(
        (item) => `
          <article class="tw-linked-activity">
            <span class="tw-linked-activity__category">${item.category}</span>
            <h3>${item.title}</h3>
            <p>${item.detail}</p>
          </article>
        `
      )
      .join("");
  }

  plan.innerHTML = getScheduleForDate(calendarState.selectedDate)
    .map(
      (item) => `
        <div class="tw-day-plan__row">
          <span class="tw-day-plan__slot">${item.slot}</span>
          <span class="tw-day-plan__detail">${item.detail}</span>
        </div>
      `
    )
    .join("");
}

function selectDateFromKey(dateKey) {
  const [year, month, day] = dateKey.split("-").map(Number);
  calendarState.selectedDate = new Date(year, month - 1, day);
  calendarState.viewDate = startOfMonth(calendarState.selectedDate);
  renderCalendar();
  renderSelectedDay();
}

function bindControls() {
  document.getElementById("calendar-prev")?.addEventListener("click", () => {
    calendarState.viewDate = addMonths(calendarState.viewDate, -1);
    renderCalendar();
  });

  document.getElementById("calendar-next")?.addEventListener("click", () => {
    calendarState.viewDate = addMonths(calendarState.viewDate, 1);
    renderCalendar();
  });

  document.getElementById("calendar-today")?.addEventListener("click", () => {
    calendarState.selectedDate = stripTime(new Date());
    calendarState.viewDate = startOfMonth(calendarState.selectedDate);
    renderCalendar();
    renderSelectedDay();
  });

  document.getElementById("account-calendar-grid")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-calendar-date]");
    if (!button) {
      return;
    }
    selectDateFromKey(button.dataset.calendarDate);
  });

  document.addEventListener("tw:language-changed", () => {
    renderWeekdays();
    renderCalendar();
    renderSelectedDay();
    renderAuthStatusCard();
  });

  document.addEventListener("tw:auth-state-changed", () => {
    renderAuthStatusCard();
  });
}

function renderAll() {
  renderAuthStatusCard();
  renderWeekdays();
  renderCalendar();
  renderSelectedDay();
}

export function initializeAccountHome() {
  if (initialized) {
    renderAll();
    return;
  }

  initialized = true;
  bindControls();
  renderAll();
}
