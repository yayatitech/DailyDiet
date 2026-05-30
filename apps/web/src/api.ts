export const DAY_KEYS = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
] as const;

export type DayKey = (typeof DAY_KEYS)[number];

export const DAY_LABELS: Record<DayKey, string> = {
  monday: "Monday",
  tuesday: "Tuesday",
  wednesday: "Wednesday",
  thursday: "Thursday",
  friday: "Friday",
  saturday: "Saturday",
  sunday: "Sunday",
};

export type TimeSlot = { id: number; label: string; time: string };
export type MealItem = { text: string; recipe_url?: string | null };
export type WeekSummary = { id: string; title: string; start_date: string | null };
export type WeekDetail = {
  id: string;
  title: string;
  start_date: string | null;
  notes: string;
  meals: Record<DayKey, MealItem[][]>;
};

export function cellId(weekId: string, day: DayKey, slotIndex: number): string {
  return `${weekId}:${day}:${slotIndex}`;
}

export function todayDayKey(week: WeekDetail): DayKey | null {
  if (!week.start_date) return null;
  const start = new Date(week.start_date + "T00:00:00");
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diff = Math.floor((today.getTime() - start.getTime()) / 86400000);
  if (diff < 0 || diff > 6) return null;
  return DAY_KEYS[diff];
}

export function getToken(): string | null {
  return localStorage.getItem("dailyDiet.accessToken");
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem("dailyDiet.accessToken", access);
  localStorage.setItem("dailyDiet.refreshToken", refresh);
}

export function clearTokens(): void {
  localStorage.removeItem("dailyDiet.accessToken");
  localStorage.removeItem("dailyDiet.refreshToken");
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(path, { ...init, headers });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  timeSlots: () => apiFetch<TimeSlot[]>("/v1/time-slots"),
  weeks: () => apiFetch<WeekSummary[]>("/v1/weeks"),
  week: (id: string) => apiFetch<WeekDetail>(`/v1/weeks/${id}`),
  patchMeal: (weekId: string, day: DayKey, slotIndex: number, content: string) =>
    apiFetch(`/v1/weeks/${weekId}/meals`, {
      method: "PATCH",
      body: JSON.stringify({ day, slot_index: slotIndex, content }),
    }),
  patchNotes: (weekId: string, notes: string) =>
    apiFetch(`/v1/weeks/${weekId}/notes`, {
      method: "PATCH",
      body: JSON.stringify({ notes }),
    }),
  resetWeek: (weekId: string) =>
    apiFetch(`/v1/weeks/${weekId}/reset`, { method: "POST" }),
  completions: (weekId: string) =>
    apiFetch<{ day: DayKey; slot_index: number; completed: boolean }[]>(
      `/v1/weeks/${weekId}/completions`
    ),
  toggleCompletion: (weekId: string, day: DayKey, slotIndex: number, completed: boolean) =>
    apiFetch(`/v1/weeks/${weekId}/completions`, {
      method: "PUT",
      body: JSON.stringify({ day, slot_index: slotIndex, completed }),
    }),
  clearCompletions: () => apiFetch("/v1/completions", { method: "DELETE" }),
  export: () => apiFetch<{ plan: unknown; tracking: Record<string, boolean>; exported_at: string }>("/v1/export"),
  import: (bundle: unknown) =>
    apiFetch("/v1/import", { method: "POST", body: JSON.stringify(bundle) }),
  login: (email: string, password: string) =>
    apiFetch<{ access_token: string; refresh_token: string }>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string) =>
    apiFetch<{ access_token: string; refresh_token: string }>("/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
};
