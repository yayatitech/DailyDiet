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

export type TimeSlot = {
  id: number;
  label: string;
  time: string;
};

export type Week = {
  id: string;
  title: string;
  meals: Record<DayKey, string[]>;
  notes: string;
};

export type MealPlan = {
  timeSlots: TimeSlot[];
  weeks: Week[];
};

export type TrackingMap = Record<string, boolean>;

export type UiState = {
  selectedWeekId: string;
  viewMode: "week" | "day";
  selectedDay: DayKey;
};

export type ExportBundle = {
  plan: MealPlan;
  tracking: TrackingMap;
  exportedAt: string;
};

export function cellId(weekId: string, day: DayKey, slotIndex: number): string {
  return `${weekId}:${day}:${slotIndex}`;
}

export function parseWeekStartDate(title: string): Date | null {
  const m = title.match(/starting:\s*(.+)$/i);
  if (!m || !m[1].trim()) return null;
  const parsed = new Date(m[1].trim());
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function todayDayKeyForWeek(week: Week): DayKey | null {
  const start = parseWeekStartDate(week.title);
  if (!start) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  start.setHours(0, 0, 0, 0);
  const diffDays = Math.floor(
    (today.getTime() - start.getTime()) / (24 * 60 * 60 * 1000)
  );
  if (diffDays < 0 || diffDays > 6) return null;
  return DAY_KEYS[diffDays];
}
