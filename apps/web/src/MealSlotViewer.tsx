import { MealItem } from "./api";
import RecipeLink from "./RecipeLink";

type Props = {
  items: MealItem[];
};

export default function MealSlotViewer({ items }: Props) {
  const rows = items.filter((item) => item.text.trim());

  if (!rows.length) {
    return <p className="meal-item-empty">—</p>;
  }

  return (
    <div className="meal-items">
      {rows.map((item, index) => (
        <div key={index} className="meal-item-row">
          <RecipeLink
            text={item.text}
            recipeUrl={item.recipe_url}
            recipeExternal={item.recipe_external}
          />
          <span className="meal-item-text">{item.text}</span>
        </div>
      ))}
    </div>
  );
}
