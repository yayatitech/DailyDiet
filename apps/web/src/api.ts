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
export type MealItem = {
  text: string;
  recipe_id?: number | null;
  recipe_url?: string | null;
  recipe_external?: boolean;
};
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

export function completionSet(
  weekId: string,
  rows: { day: DayKey; slot_index: number }[]
): Set<string> {
  return new Set(rows.map((r) => cellId(weekId, r.day, r.slot_index)));
}

export function todayDayKey(week: Pick<WeekDetail, "start_date">): DayKey | null {
  return dayKeyForWeekOnDate(week);
}

export function dayKeyForWeekOnDate(
  week: Pick<WeekSummary, "start_date">,
  date: Date = new Date()
): DayKey | null {
  if (!week.start_date) return null;
  const start = new Date(week.start_date + "T00:00:00");
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  const diff = Math.floor((d.getTime() - start.getTime()) / 86400000);
  if (diff < 0 || diff > 6) return null;
  return DAY_KEYS[diff];
}

/** Pick the template week whose date range includes today, else the first week. */
export function weekForToday(weeks: WeekSummary[]): WeekSummary | null {
  for (const w of weeks) {
    if (dayKeyForWeekOnDate(w) !== null) return w;
  }
  return weeks[0] ?? null;
}

export function formatTodayHeading(day: DayKey | null): string {
  const d = new Date();
  const dateStr = d.toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric", year: "numeric" });
  if (!day) return `Today — ${dateStr}`;
  return `Today — ${DAY_LABELS[day]}, ${dateStr}`;
}

export type Ingredient = { amount: string; item: string };

export type RecipeSummary = {
  id: number;
  name: string;
  display_name: string | null;
  has_image: boolean;
  has_content: boolean;
};

export type RecipeDetail = {
  id: number;
  name: string;
  name_key: string;
  display_name: string | null;
  ingredients: Ingredient[];
  instructions: string;
  image_url: string | null;
  external_url: string | null;
  has_content: boolean;
  updated_at: string | null;
};

export type RecipeInput = {
  name: string;
  display_name?: string | null;
  ingredients?: Ingredient[];
  instructions?: string;
  external_url?: string | null;
};

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
    ...(init?.headers as Record<string, string>),
  };
  if (!(init?.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
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
  recipes: () => apiFetch<RecipeSummary[]>("/v1/recipes"),
  recipe: (id: number) => apiFetch<RecipeDetail>(`/v1/recipes/${id}`),
  createRecipe: (adminKey: string, body: RecipeInput) =>
    apiFetch<RecipeDetail>("/v1/admin/recipes", {
      method: "POST",
      headers: { "X-Admin-Key": adminKey },
      body: JSON.stringify(body),
    }),
  updateRecipe: (adminKey: string, id: number, body: Partial<RecipeInput>) =>
    apiFetch<RecipeDetail>(`/v1/admin/recipes/${id}`, {
      method: "PATCH",
      headers: { "X-Admin-Key": adminKey },
      body: JSON.stringify(body),
    }),
  uploadRecipeImage: (adminKey: string, id: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiFetch<RecipeDetail>(`/v1/admin/recipes/${id}/image`, {
      method: "POST",
      headers: { "X-Admin-Key": adminKey },
      body: form,
    });
  },
  deleteRecipe: (adminKey: string, id: number) =>
    apiFetch(`/v1/admin/recipes/${id}`, {
      method: "DELETE",
      headers: { "X-Admin-Key": adminKey },
    }),
};
