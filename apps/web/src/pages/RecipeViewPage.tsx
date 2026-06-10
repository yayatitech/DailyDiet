import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getAdminKey } from "../adminKey";
import { api, RecipeDetail } from "../api";
import RecipePageShell from "./RecipePageShell";

export default function RecipeViewPage() {
  const { id } = useParams();
  const recipeId = Number(id);
  const [recipe, setRecipe] = useState<RecipeDetail | null>(null);
  const [error, setError] = useState("");
  const hasAdminKey = Boolean(getAdminKey().trim());

  useEffect(() => {
    if (!Number.isFinite(recipeId)) {
      setError("Invalid recipe id");
      return;
    }
    (async () => {
      try {
        setRecipe(await api.recipe(recipeId));
        setError("");
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [recipeId]);

  const title = recipe?.display_name || recipe?.name || "Recipe";

  return (
    <>
      <RecipePageShell title={title}>
        <div className="recipe-page-actions">
          {hasAdminKey && recipe && (
            <Link to={`/recipes/${recipe.id}/edit`} className="btn secondary">
              Edit
            </Link>
          )}
          {recipe?.external_url && (
            <a
              className="btn secondary"
              href={recipe.external_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              External link ↗
            </a>
          )}
        </div>
      </RecipePageShell>

      <main className="recipe-page-body">
        {error && <p className="error">{error}</p>}
        {recipe && (
          <article className="recipe-view">
            {recipe.image_url && (
              <img className="recipe-hero-image" src={recipe.image_url} alt={title} />
            )}
            {recipe.display_name && recipe.display_name !== recipe.name && (
              <p className="recipe-canonical-name">Meal name: {recipe.name}</p>
            )}
            {recipe.ingredients.length > 0 && (
              <section>
                <h2>Ingredients</h2>
                <ul className="recipe-ingredients">
                  {recipe.ingredients.map((ing, i) => (
                    <li key={i}>
                      {ing.amount ? `${ing.amount} ` : ""}
                      {ing.item}
                    </li>
                  ))}
                </ul>
              </section>
            )}
            {recipe.instructions && (
              <section>
                <h2>Instructions</h2>
                <p className="recipe-instructions">{recipe.instructions}</p>
              </section>
            )}
            {!recipe.has_content && !recipe.external_url && (
              <p className="recipe-empty">No recipe content yet.</p>
            )}
          </article>
        )}
      </main>
    </>
  );
}
