import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { Link } from "react-router-dom";
import { RecipeSummary } from "./api";

export function normalizeMealName(name: string): string {
  return name.trim().toLowerCase().replace(/\s+/g, " ");
}

function recipeMatchesQuery(recipe: RecipeSummary, query: string): boolean {
  const q = normalizeMealName(query);
  if (!q) return true;
  const label = recipe.display_name || recipe.name;
  return normalizeMealName(recipe.name).includes(q) || normalizeMealName(label).includes(q);
}

function recipeMatchesValue(recipes: RecipeSummary[], value: string): boolean {
  const key = normalizeMealName(value);
  if (!key) return false;
  return recipes.some((r) => normalizeMealName(r.name) === key);
}

type Props = {
  recipes: RecipeSummary[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

export default function RecipeCombobox({ recipes, value, onChange, placeholder = "Meal item" }: Props) {
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);

  const filtered = useMemo(
    () => (open ? recipes.filter((r) => recipeMatchesQuery(r, value)) : []),
    [open, recipes, value]
  );

  const showCreate = value.trim().length > 0 && !recipeMatchesValue(recipes, value);

  useEffect(() => {
    setHighlight(0);
  }, [value, filtered.length]);

  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const selectRecipe = (recipe: RecipeSummary) => {
    onChange(recipe.name);
    setOpen(false);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      setOpen(false);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!open) setOpen(true);
      else setHighlight((i) => Math.min(i + 1, Math.max(filtered.length - 1, 0)));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((i) => Math.max(i - 1, 0));
      return;
    }
    if (e.key === "Enter" && open && filtered.length > 0) {
      e.preventDefault();
      selectRecipe(filtered[highlight]);
    }
  };

  return (
    <div className="recipe-combobox" ref={rootRef}>
      <input
        type="text"
        className="meal-item-input recipe-combobox-input"
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
        placeholder={placeholder}
        role="combobox"
        aria-expanded={open}
        aria-autocomplete="list"
        aria-controls={open ? "recipe-combobox-list" : undefined}
      />
      {open && filtered.length > 0 && (
        <ul className="recipe-combobox-list" id="recipe-combobox-list" role="listbox">
          {filtered.map((recipe, index) => {
            const label = recipe.display_name || recipe.name;
            const sub = recipe.display_name && recipe.display_name !== recipe.name ? recipe.name : null;
            return (
              <li key={recipe.id} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={index === highlight}
                  className={`recipe-combobox-option${index === highlight ? " highlighted" : ""}`}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => selectRecipe(recipe)}
                  onMouseEnter={() => setHighlight(index)}
                >
                  <span className="recipe-combobox-option-label">{label}</span>
                  {sub && <span className="recipe-combobox-option-sub">{sub}</span>}
                </button>
              </li>
            );
          })}
        </ul>
      )}
      {showCreate && (
        <Link
          className="recipe-combobox-create"
          to={`/recipes/new?name=${encodeURIComponent(value.trim())}`}
          onClick={() => setOpen(false)}
        >
          Create recipe &ldquo;{value.trim()}&rdquo;
        </Link>
      )}
    </div>
  );
}
