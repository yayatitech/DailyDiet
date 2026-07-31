import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminKey, setAdminKey } from "../adminKey";
import { api, RecipeSummary } from "../api";
import { normalizeMealName } from "../RecipeCombobox";
import RecipePageShell from "./RecipePageShell";

export default function RecipeListPage() {
  const [adminKey, setAdminKeyState] = useState(getAdminKey);
  const [recipes, setRecipes] = useState<RecipeSummary[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const loadRecipes = useCallback(async () => {
    try {
      setRecipes(await api.recipes());
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    loadRecipes();
  }, [loadRecipes]);

  const filtered = useMemo(() => {
    const q = normalizeMealName(search);
    if (!q) return recipes;
    return recipes.filter((r) => {
      const label = r.display_name || r.name;
      return (
        normalizeMealName(r.name).includes(q) ||
        normalizeMealName(label).includes(q)
      );
    });
  }, [recipes, search]);

  const saveKey = (key: string) => {
    setAdminKeyState(key);
    setAdminKey(key);
  };

  const remove = async (id: number) => {
    if (!adminKey.trim()) {
      setError("Admin key required");
      return;
    }
    if (!window.confirm("Delete this recipe?")) return;
    setLoading(true);
    try {
      await api.deleteRecipe(adminKey.trim(), id);
      await loadRecipes();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <RecipePageShell title="Recipes">
        <div className="recipe-page-actions">
          <Link to="/recipes/new" className="btn">
            Add recipe
          </Link>
        </div>
      </RecipePageShell>

      <main className="recipe-page-body">
        <p className="panel-hint">
          Manage full recipe content. Meal names must match meal-plan item text for automatic linking.
        </p>

        <label className="control recipe-search">
          <span>Search recipes</span>
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter by name…"
            autoComplete="off"
          />
        </label>

        <label className="control admin-key-control">
          <span className="label-required">Admin key</span>
          <input
            type="password"
            value={adminKey}
            onChange={(e) => saveKey(e.target.value)}
            placeholder="X-Admin-Key"
            autoComplete="off"
          />
        </label>

        {error && <p className="error">{error}</p>}

        <ul className="recipe-admin-list">
          {filtered.map((r) => (
            <li key={r.id} className="recipe-admin-item">
              <div className="recipe-admin-main">
                <strong>{r.display_name || r.name}</strong>
                {r.display_name && r.display_name !== r.name && (
                  <span className="recipe-admin-subname">({r.name})</span>
                )}
                <span className="recipe-admin-badges">
                  {r.has_content ? "Page" : "External only"}
                  {r.has_image ? " · Photo" : ""}
                </span>
              </div>
              <div className="recipe-admin-actions">
                <Link to={`/recipes/${r.id}`} className="btn secondary recipe-btn">
                  View
                </Link>
                <Link to={`/recipes/${r.id}/edit`} className="btn secondary recipe-btn">
                  Edit
                </Link>
                <button
                  type="button"
                  className="btn secondary recipe-btn"
                  disabled={loading}
                  onClick={() => remove(r.id)}
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
          {!recipes.length && <li className="recipe-list-empty">No recipes yet.</li>}
          {!!recipes.length && !filtered.length && (
            <li className="recipe-list-empty">No recipes match your search.</li>
          )}
        </ul>
      </main>
    </>
  );
}
