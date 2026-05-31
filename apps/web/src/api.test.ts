import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { cellId, completionSet, todayDayKey, type DayKey, type WeekDetail } from "./api";

describe("cellId", () => {
  it("formats week day slot id", () => {
    expect(cellId("week-1", "monday", 0)).toBe("week-1:monday:0");
  });
});

describe("todayDayKey", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  const week = (start_date: string | null): WeekDetail => ({
    id: "week-1",
    title: "Week 1",
    start_date,
    notes: "",
    meals: {} as WeekDetail["meals"],
  });

  it("returns null when start_date is missing", () => {
    expect(todayDayKey(week(null))).toBeNull();
  });

  it("returns monday on start date", () => {
    vi.setSystemTime(new Date("2025-01-06T12:00:00"));
    expect(todayDayKey(week("2025-01-06"))).toBe("monday");
  });

  it("returns wednesday three days after start", () => {
    vi.setSystemTime(new Date("2025-01-08T12:00:00"));
    expect(todayDayKey(week("2025-01-06"))).toBe("wednesday");
  });

  it("returns null before start date", () => {
    vi.setSystemTime(new Date("2025-01-05T12:00:00"));
    expect(todayDayKey(week("2025-01-06"))).toBeNull();
  });

  it("returns null after day 6", () => {
    vi.setSystemTime(new Date("2025-01-14T12:00:00"));
    expect(todayDayKey(week("2025-01-06"))).toBeNull();
  });
});

describe("completionSet", () => {
  it("maps rows to cell id set", () => {
    const rows = [
      { day: "monday" as DayKey, slot_index: 0 },
      { day: "tuesday" as DayKey, slot_index: 2 },
    ];
    const result = completionSet("week-1", rows);
    expect(result).toEqual(new Set(["week-1:monday:0", "week-1:tuesday:2"]));
  });

  it("returns empty set for no rows", () => {
    expect(completionSet("week-1", [])).toEqual(new Set());
  });
});
