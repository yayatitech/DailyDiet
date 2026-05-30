import { renderApp, type AppHandlers } from "./render";
import {
  buildExportBundle,
  importBundle,
  initPlan,
  loadTracking,
  loadUi,
  resetTracking,
  resetWeekToSeed,
  savePlan,
  saveTracking,
  saveUi,
} from "./storage";
import type { ExportBundle, MealPlan, TrackingMap, UiState } from "./types";
import { DAY_KEYS, cellId } from "./types";

const rootEl = document.getElementById("app");
if (!rootEl) throw new Error("#app not found");
const root: HTMLElement = rootEl;

let plan: MealPlan;
let tracking: TrackingMap;
let ui: UiState;

let savePlanTimer: ReturnType<typeof setTimeout> | null = null;

function getSelectedWeek() {
  const week = plan.weeks.find((w) => w.id === ui.selectedWeekId);
  if (!week) throw new Error("Week not found");
  return week;
}

function persistUi(): void {
  saveUi(ui);
}

function debouncedSavePlan(): void {
  if (savePlanTimer) clearTimeout(savePlanTimer);
  savePlanTimer = setTimeout(() => {
    savePlan(plan);
    savePlanTimer = null;
  }, 300);
}

function refresh(): void {
  renderApp(root, plan, getSelectedWeek(), tracking, ui, handlers);
}

const handlers: AppHandlers = {
  onWeekChange(weekId) {
    ui.selectedWeekId = weekId;
    persistUi();
    refresh();
  },
  onViewModeChange(mode) {
    ui.viewMode = mode;
    persistUi();
    refresh();
  },
  onDayChange(day) {
    ui.selectedDay = day;
    persistUi();
    refresh();
  },
  onMealChange(day, slotIndex, value) {
    const week = getSelectedWeek();
    week.meals[day][slotIndex] = value;
    debouncedSavePlan();
  },
  onNotesChange(value) {
    getSelectedWeek().notes = value;
    debouncedSavePlan();
  },
  onTrackToggle(day, slotIndex, checked) {
    const week = getSelectedWeek();
    const id = cellId(week.id, day, slotIndex);
    if (checked) tracking[id] = true;
    else delete tracking[id];
    saveTracking(tracking);
  },
  onResetWeek() {
    if (!confirm("Reset this week’s meals and notes to the original seed?")) return;
    const updated = resetWeekToSeed(ui.selectedWeekId);
    if (updated) {
      plan = updated;
      refresh();
    }
  },
  onResetTracking() {
    if (!confirm("Clear all meal checkboxes?")) return;
    resetTracking();
    tracking = {};
    refresh();
  },
  onExport() {
    const bundle = buildExportBundle(plan, tracking);
    const blob = new Blob([JSON.stringify(bundle, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dailydiet-backup-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  },
  onImport(file) {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const bundle = JSON.parse(reader.result as string) as ExportBundle;
        if (!bundle.plan?.weeks) throw new Error("Invalid backup");
        importBundle(bundle);
        plan = bundle.plan;
        tracking = bundle.tracking ?? {};
        ui.selectedWeekId = plan.weeks[0]?.id ?? ui.selectedWeekId;
        persistUi();
        refresh();
      } catch {
        alert("Could not import file. Use a DailyDiet export JSON.");
      }
    };
    reader.readAsText(file);
  },
};

async function boot(): Promise<void> {
  plan = await initPlan();
  tracking = loadTracking();

  const savedUi = loadUi();
  ui = {
    selectedWeekId:
      savedUi.selectedWeekId && plan.weeks.some((w) => w.id === savedUi.selectedWeekId)
        ? savedUi.selectedWeekId
        : plan.weeks[0]?.id ?? "week-1",
    viewMode: savedUi.viewMode ?? "week",
    selectedDay: savedUi.selectedDay ?? "monday",
  };

  if (!DAY_KEYS.includes(ui.selectedDay)) ui.selectedDay = "monday";

  refresh();
}

boot().catch((err) => {
  root.innerHTML = `<p class="error">Failed to load: ${err instanceof Error ? err.message : String(err)}</p>`;
});
