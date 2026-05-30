import { MealItem } from "./api";

type Props = {
  items: MealItem[];
  onChange: (items: MealItem[]) => void;
};

export default function MealSlotEditor({ items, onChange }: Props) {
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
          {item.recipe_url ? (
            <a
              className="recipe-link"
              href={item.recipe_url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Recipe for ${item.text}`}
              title={`Recipe for ${item.text}`}
            >
              ↗
            </a>
          ) : (
            <span className="recipe-link-placeholder" aria-hidden="true" />
          )}
          <input
            type="text"
            className="meal-item-input"
            value={item.text}
            onChange={(e) => updateItem(index, e.target.value)}
            placeholder="Meal item"
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
