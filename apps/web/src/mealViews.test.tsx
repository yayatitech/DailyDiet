import { renderToStaticMarkup } from "react-dom/server";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { MealSlotCell as WeekMealSlotCell } from "./App";
import DayMealsView from "./DayMealsView";

const meal = { text: "Apple and almonds" };
const slots = Array.from({ length: 8 }, (_, id) => ({
  id,
  label: `Meal ${id + 1}`,
  time: `${id + 8}:00`,
}));
const meals = Array.from({ length: 8 }, (_, index) => index === 0 ? [meal] : []);

function render(view: ReactNode): string {
  return renderToStaticMarkup(<MemoryRouter>{view}</MemoryRouter>);
}

describe("meal views", () => {
  it("renders meal content without checkboxes in the Week grid", () => {
    const html = render(
      <WeekMealSlotCell items={[meal]} isView recipes={[]} onChange={() => undefined} />,
    );

    expect(html).toContain("Apple and almonds");
    expect(html).not.toContain('type="checkbox"');
  });

  it.each(["Today", "Day view"])("renders meal content without checkboxes in %s", () => {
    const html = render(
      <DayMealsView
        day="monday"
        weekMeals={meals}
        slots={slots}
        isView
        recipes={[]}
        onChange={() => undefined}
      />,
    );

    expect(html).toContain("Apple and almonds");
    expect(html).not.toContain('type="checkbox"');
  });

  it("retains meal editing in the Week grid and Day view", () => {
    const weekHtml = render(
      <WeekMealSlotCell items={[meal]} isView={false} recipes={[]} onChange={() => undefined} />,
    );
    const dayHtml = render(
      <DayMealsView
        day="monday"
        weekMeals={meals}
        slots={slots}
        isView={false}
        recipes={[]}
        onChange={() => undefined}
      />,
    );

    expect(weekHtml).toContain('value="Apple and almonds"');
    expect(dayHtml).toContain('value="Apple and almonds"');
    expect(dayHtml).toContain("+ Add item");
  });
});
