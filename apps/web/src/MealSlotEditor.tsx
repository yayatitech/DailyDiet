import { MealItem, RecipeSummary } from "./api";
import RecipeCombobox from "./RecipeCombobox";
import RecipeLink from "./RecipeLink";

type Props = {
  items: MealItem[];
  recipes: RecipeSummary[];
  onChange: (items: MealItem[]) => void;
};

export default function MealSlotEditor({ items, recipes, onChange }: Props) {
  const rows = items.length ? items : [{ text: "", recipe_url: null }];

  const updateItem = (index: number, text: string) => {
    const next = rows.map((item, i) => (i === index ? { ...item, text } : item));
    onChange(next);
  };

  const addItem = () => {
    onChange([...rows, { text: "", recipe_url: null }]);
  };

  const removeItem = (index: number) => {
    const next = rows.filter((_, i) => i !== index);
    onChange(next.length ? next : [{ text: "", recipe_url: null }]);
  };

  return (
    <div className="meal-items">
      {rows.map((item, index) => (
        <div key={index} className="meal-item-row">
          <RecipeLink
            text={item.text}
            recipeUrl={item.recipe_url}
            recipeExternal={item.recipe_external}
          />
          <RecipeCombobox
            recipes={recipes}
            value={item.text}
            onChange={(text) => updateItem(index, text)}
          />
          <button
            type="button"
            className="meal-item-remove"
            onClick={() => removeItem(index)}
            aria-label="Remove meal item"
            title="Remove"
          >
            ×
          </button>
        </div>
      ))}
      <button type="button" className="meal-item-add" onClick={addItem} aria-label="Add meal item">
        + Add item
      </button>
    </div>
  );
}

export function itemsToContent(items: MealItem[]): string {
  return items
    .map((item) => item.text.trim())
    .filter(Boolean)
    .join("\n");
}
