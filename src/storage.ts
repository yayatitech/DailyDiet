import type { ExportBundle, MealPlan, TrackingMap, UiState } from "./types";
import { DAY_KEYS } from "./types";

const PLAN_KEY = "dailyDiet.plan";
const TRACKING_KEY = "dailyDiet.tracking";
const UI_KEY = "dailyDiet.ui";
const SEED_KEY = "dailyDiet.seed";

let seedPlan: MealPlan | null = null;

function readJson<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function writeJson(key: string, value: unknown): void {
  localStorage.setItem(key, JSON.stringify(value));
}

export async function loadSeedPlan(): Promise<MealPlan> {
  const res = await fetch("/data/meal-plan.json");
  if (!res.ok) throw new Error("Failed to load meal plan seed");
  const plan = (await res.json()) as MealPlan;
  seedPlan = plan;
  return structuredClone(plan);
}

export function getSeedPlan(): MealPlan | null {
  return seedPlan ? structuredClone(seedPlan) : null;
}

export function loadPlan(): MealPlan | null {
  return readJson<MealPlan>(PLAN_KEY);
}

export function savePlan(plan: MealPlan): void {
  writeJson(PLAN_KEY, plan);
  if (seedPlan) {
    writeJson(SEED_KEY, { version: seedPlan.weeks.length });
  }
}

export function loadTracking(): TrackingMap {
  return readJson<TrackingMap>(TRACKING_KEY) ?? {};
}

export function saveTracking(tracking: TrackingMap): void {
  writeJson(TRACKING_KEY, tracking);
}

export function loadUi(): Partial<UiState> {
  return readJson<Partial<UiState>>(UI_KEY) ?? {};
}

export function saveUi(ui: UiState): void {
  writeJson(UI_KEY, ui);
}

export async function initPlan(): Promise<MealPlan> {
  await loadSeedPlan();
  const stored = loadPlan();
  if (stored) return stored;
  const seed = getSeedPlan();
  if (!seed) throw new Error("Seed plan not loaded");
  return seed;
}

export function resetWeekToSeed(weekId: string): MealPlan | null {
  const current = loadPlan() ?? getSeedPlan();
  const seed = getSeedPlan();
  if (!current || !seed) return null;

  const seedWeek = seed.weeks.find((w) => w.id === weekId);
  const idx = current.weeks.findIndex((w) => w.id === weekId);
  if (!seedWeek || idx === -1) return null;

  current.weeks[idx] = structuredClone(seedWeek);
  savePlan(current);
  return current;
}

export function resetTracking(): void {
  localStorage.removeItem(TRACKING_KEY);
}

export function resetPlanToSeed(): MealPlan | null {
  const seed = getSeedPlan();
  if (!seed) return null;
  const clone = structuredClone(seed);
  savePlan(clone);
  return clone;
}

export function buildExportBundle(plan: MealPlan, tracking: TrackingMap): ExportBundle {
  return {
    plan,
    tracking,
    exportedAt: new Date().toISOString(),
  };
}

export function importBundle(bundle: ExportBundle): void {
  const plan = bundle.plan;
  for (const week of plan.weeks) {
    for (const day of DAY_KEYS) {
      while (week.meals[day].length < 8) week.meals[day].push("");
      week.meals[day] = week.meals[day].slice(0, 8);
    }
  }
  savePlan(plan);
  saveTracking(bundle.tracking ?? {});
}
