import type { DayKey, MealPlan, TrackingMap, UiState, Week } from "./types";
import {
  DAY_KEYS,
  DAY_LABELS,
  cellId,
  todayDayKeyForWeek,
} from "./types";

export type AppHandlers = {
  onWeekChange: (weekId: string) => void;
  onViewModeChange: (mode: "week" | "day") => void;
  onDayChange: (day: DayKey) => void;
  onMealChange: (day: DayKey, slotIndex: number, value: string) => void;
  onNotesChange: (value: string) => void;
  onTrackToggle: (day: DayKey, slotIndex: number, checked: boolean) => void;
  onResetWeek: () => void;
  onResetTracking: () => void;
  onExport: () => void;
  onImport: (file: File) => void;
};

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function slotHeader(plan: MealPlan, slotIndex: number): string {
  const slot = plan.timeSlots[slotIndex];
  if (!slot) return `Meal ${slotIndex + 1}`;
  return `${slot.label}<span class="slot-time">${escapeHtml(slot.time)}</span>`;
}

function isTracked(tracking: TrackingMap, weekId: string, day: DayKey, slot: number): boolean {
  return !!tracking[cellId(weekId, day, slot)];
}

function mealCell(
  week: Week,
  day: DayKey,
  slotIndex: number,
  tracking: TrackingMap,
  todayDay: DayKey | null
): string {
  const id = cellId(week.id, day, slotIndex);
  const meal = week.meals[day][slotIndex] ?? "";
  const checked = isTracked(tracking, week.id, day, slotIndex);
  const todayClass = todayDay === day ? " col-today" : "";
  const doneClass = checked ? " cell-done" : "";

  return `
    <td class="meal-cell${todayClass}${doneClass}" data-day="${day}" data-slot="${slotIndex}">
      <label class="cell-label">
        <input type="checkbox" class="track-cb" data-cell-id="${id}" ${checked ? "checked" : ""} aria-label="Mark meal done" />
        <textarea class="meal-input" rows="3" aria-label="${DAY_LABELS[day]} meal ${slotIndex + 1}">${escapeHtml(meal)}</textarea>
      </label>
    </td>`;
}

function weekGrid(plan: MealPlan, week: Week, tracking: TrackingMap): string {
  const todayDay = todayDayKeyForWeek(week);
  const headerCells = DAY_KEYS.map(
    (d) =>
      `<th class="${todayDay === d ? "col-today" : ""}">${DAY_LABELS[d]}</th>`
  ).join("");

  const rows = Array.from({ length: 8 }, (_, slotIndex) => {
    const cells = DAY_KEYS.map((day) =>
      mealCell(week, day, slotIndex, tracking, todayDay)
    ).join("");
    return `
      <tr>
        <th class="slot-header" scope="row">${slotHeader(plan, slotIndex)}</th>
        ${cells}
      </tr>`;
  }).join("");

  return `
    <div class="grid-wrap">
      <table class="meal-grid" aria-label="Weekly meal plan">
        <thead>
          <tr>
            <th scope="col">Time slot</th>
            ${headerCells}
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

function dayView(
  plan: MealPlan,
  week: Week,
  day: DayKey,
  tracking: TrackingMap
): string {
  const items = Array.from({ length: 8 }, (_, slotIndex) => {
    const slot = plan.timeSlots[slotIndex];
    const meal = week.meals[day][slotIndex] ?? "";
    const checked = isTracked(tracking, week.id, day, slotIndex);
    const id = cellId(week.id, day, slotIndex);
    const doneClass = checked ? " cell-done" : "";

    return `
      <article class="day-slot${doneClass}" data-day="${day}" data-slot="${slotIndex}">
        <header class="day-slot-header">
          <span class="day-slot-title">${slot?.label ?? `Meal ${slotIndex + 1}`}</span>
          <span class="day-slot-time">${escapeHtml(slot?.time ?? "")}</span>
        </header>
        <label class="cell-label">
          <input type="checkbox" class="track-cb" data-cell-id="${id}" ${checked ? "checked" : ""} />
          <span class="track-label">Done</span>
          <textarea class="meal-input" rows="3">${escapeHtml(meal)}</textarea>
        </label>
      </article>`;
  }).join("");

  return `<div class="day-view">${items}</div>`;
}

export function renderApp(
  root: HTMLElement,
  plan: MealPlan,
  week: Week,
  tracking: TrackingMap,
  ui: UiState,
  handlers: AppHandlers
): void {
  const weekOptions = plan.weeks
    .map(
      (w) =>
        `<option value="${w.id}" ${w.id === ui.selectedWeekId ? "selected" : ""}>${escapeHtml(w.title)}</option>`
    )
    .join("");

  const dayOptions = DAY_KEYS.map(
    (d) =>
      `<option value="${d}" ${d === ui.selectedDay ? "selected" : ""}>${DAY_LABELS[d]}</option>`
  ).join("");

  const mainContent =
    ui.viewMode === "week"
      ? weekGrid(plan, week, tracking)
      : dayView(plan, week, ui.selectedDay, tracking);

  root.innerHTML = `
    <header class="app-header">
      <div class="brand">
        <h1>DailyDiet</h1>
        <p class="subtitle">Fitelo Weekly Meal Plan</p>
      </div>
      <div class="controls">
        <label class="control">
          <span>Week</span>
          <select id="week-select">${weekOptions}</select>
        </label>
        <div class="view-toggle" role="group" aria-label="View mode">
          <button type="button" class="view-btn ${ui.viewMode === "week" ? "active" : ""}" data-view="week">Week grid</button>
          <button type="button" class="view-btn ${ui.viewMode === "day" ? "active" : ""}" data-view="day">Day view</button>
        </div>
        <label class="control day-picker ${ui.viewMode === "day" ? "" : "hidden"}">
          <span>Day</span>
          <select id="day-select">${dayOptions}</select>
        </label>
      </div>
      <div class="actions">
        <button type="button" id="btn-reset-week" class="btn secondary">Reset week</button>
        <button type="button" id="btn-reset-tracking" class="btn secondary">Reset tracking</button>
        <button type="button" id="btn-export" class="btn">Export JSON</button>
        <label class="btn secondary import-label">
          Import JSON
          <input type="file" id="import-file" accept="application/json,.json" hidden />
        </label>
      </div>
    </header>
    <main class="app-main">
      <h2 class="week-title">${escapeHtml(week.title)}</h2>
      ${mainContent}
      <section class="notes-section">
        <label for="week-notes">Notes</label>
        <textarea id="week-notes" rows="3" placeholder="Week notes…">${escapeHtml(week.notes)}</textarea>
      </section>
    </main>
  `;

  root.querySelector("#week-select")?.addEventListener("change", (e) => {
    handlers.onWeekChange((e.target as HTMLSelectElement).value);
  });

  root.querySelector("#day-select")?.addEventListener("change", (e) => {
    handlers.onDayChange((e.target as HTMLSelectElement).value as DayKey);
  });

  root.querySelectorAll(".view-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const mode = (btn as HTMLElement).dataset.view as "week" | "day";
      handlers.onViewModeChange(mode);
    });
  });

  root.querySelector("#btn-reset-week")?.addEventListener("click", () => handlers.onResetWeek());
  root.querySelector("#btn-reset-tracking")?.addEventListener("click", () => handlers.onResetTracking());
  root.querySelector("#btn-export")?.addEventListener("click", () => handlers.onExport());

  root.querySelector("#import-file")?.addEventListener("change", (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) handlers.onImport(file);
    (e.target as HTMLInputElement).value = "";
  });

  root.querySelector("#week-notes")?.addEventListener("input", (e) => {
    handlers.onNotesChange((e.target as HTMLTextAreaElement).value);
  });

  root.querySelectorAll(".meal-input").forEach((el) => {
    const textarea = el as HTMLTextAreaElement;
    const container = textarea.closest("[data-day][data-slot]");
    if (!container) return;
    const day = container.getAttribute("data-day") as DayKey;
    const slot = Number(container.getAttribute("data-slot"));

    textarea.addEventListener("input", () => {
      handlers.onMealChange(day, slot, textarea.value);
    });
  });

  root.querySelectorAll(".track-cb").forEach((el) => {
    el.addEventListener("change", () => {
      const cb = el as HTMLInputElement;
      const container = cb.closest("[data-day][data-slot]");
      if (!container) return;
      const day = container.getAttribute("data-day") as DayKey;
      const slot = Number(container.getAttribute("data-slot"));
      handlers.onTrackToggle(day, slot, cb.checked);
      container.classList.toggle("cell-done", cb.checked);
    });
  });
}
