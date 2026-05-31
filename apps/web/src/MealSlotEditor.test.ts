import { describe, expect, it } from "vitest";

import { itemsToContent } from "./MealSlotEditor";

describe("itemsToContent", () => {
  it("trims lines and joins with newline", () => {
    const result = itemsToContent([
      { text: " apple " },
      { text: "banana" },
    ]);
    expect(result).toBe("apple\nbanana");
  });

  it("drops empty lines", () => {
    const result = itemsToContent([
      { text: "apple" },
      { text: "  " },
      { text: "" },
      { text: "banana" },
    ]);
    expect(result).toBe("apple\nbanana");
  });

  it("returns empty string for no items", () => {
    expect(itemsToContent([])).toBe("");
  });
});
