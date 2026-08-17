import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { getAdminKey, setAdminKey } from "../adminKey";
import { api, Ingredient, mediaUrl, RecipeDetail } from "../api";
import RecipePageShell from "./RecipePageShell";

const emptyIngredient = (): Ingredient => ({ amount: "", item: "" });

export default function RecipeEditPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isNew = !id || id === "new";
  const recipeId = isNew ? null : Number(id);

  const [adminKey, setAdminKeyState] = useState(getAdminKey);
  const [name, setName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [ingredients, setIngredients] = useState<Ingredient[]>([emptyIngredient()]);
  const [instructions, setInstructions] = useState("");
  const [externalUrl, setExternalUrl] = useState("");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isNew) return;
    const preset = searchParams.get("name")?.trim();
    if (preset) setName(preset);
  }, [isNew, searchParams]);

  useEffect(() => {
    if (isNew || !Number.isFinite(recipeId)) return;
    (async () => {
      try {
        const recipe = await api.recipe(recipeId!);
        setName(recipe.name);
        setDisplayName(recipe.display_name ?? "");
        setIngredients(recipe.ingredients.length ? recipe.ingredients : [emptyIngredient()]);
        setInstructions(recipe.instructions);
        setExternalUrl(recipe.external_url ?? "");
        setImageUrl(mediaUrl(recipe.image_url));
        setError("");
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [isNew, recipeId]);

  const saveKey = (key: string) => {
    setAdminKeyState(key);
    setAdminKey(key);
  };

  const updateIngredient = (index: number, field: keyof Ingredient, value: string) => {
    setIngredients((rows) => rows.map((row, i) => (i === index ? { ...row, [field]: value } : row)));
  };

  const addIngredient = () => setIngredients((rows) => [...rows, emptyIngredient()]);

  const removeIngredient = (index: number) => {
    setIngredients((rows) => {
      const next = rows.filter((_, i) => i !== index);
      return next.length ? next : [emptyIngredient()];
    });
  };

  const buildBody = () => ({
    name: name.trim(),
    display_name: displayName.trim() || null,
    ingredients: ingredients.filter((ing) => ing.item.trim()),
    instructions: instructions.trim(),
    external_url: externalUrl.trim() || null,
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!adminKey.trim()) {
      setError("Admin key required");
      return;
    }
    if (!name.trim()) {
      setError("Name is required");
      return;
    }

    setLoading(true);
    try {
      let saved: RecipeDetail;
      if (isNew) {
        saved = await api.createRecipe(adminKey.trim(), buildBody());
      } else {
        saved = await api.updateRecipe(adminKey.trim(), recipeId!, buildBody());
      }
      if (imageFile) {
        saved = await api.uploadRecipeImage(adminKey.trim(), saved.id, imageFile);
      }
      navigate(`/recipes/${saved.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <RecipePageShell title={isNew ? "New recipe" : "Edit recipe"}>
        <div className="recipe-page-actions">
          {!isNew && recipeId && (
            <Link to={`/recipes/${recipeId}`} className="btn secondary">
              View
            </Link>
          )}
          <Link to="/recipes" className="btn secondary">
            All recipes
          </Link>
        </div>
      </RecipePageShell>

      <main className="recipe-page-body">
        <form className="recipe-form" onSubmit={handleSubmit}>
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

          <label className="control">
            <span className="label-required">Name (matches meal plan)</span>
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>

          <label className="control">
            <span>Display name</span>
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Optional title for recipe page"
            />
          </label>

          <fieldset className="recipe-fieldset">
            <legend>Ingredients</legend>
            {ingredients.map((ing, index) => (
              <div key={index} className="ingredient-row">
                <input
                  className="ingredient-amount"
                  placeholder="Amount"
                  value={ing.amount}
                  onChange={(e) => updateIngredient(index, "amount", e.target.value)}
                />
                <input
                  className="ingredient-item"
                  placeholder="Ingredient"
                  value={ing.item}
                  onChange={(e) => updateIngredient(index, "item", e.target.value)}
                />
                <button type="button" className="btn secondary recipe-btn" onClick={() => removeIngredient(index)}>
                  Remove
                </button>
              </div>
            ))}
            <button type="button" className="btn secondary" onClick={addIngredient}>
              Add ingredient
            </button>
          </fieldset>

          <label className="control">
            <span>Instructions</span>
            <textarea
              rows={10}
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="Markdown: ### Section heading, then - bullet steps"
            />
          </label>

          <label className="control">
            <span>External URL (fallback link)</span>
            <input
              value={externalUrl}
              onChange={(e) => setExternalUrl(e.target.value)}
              placeholder="https://..."
            />
          </label>

          <label className="control">
            <span>Photo</span>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => {
                const file = e.target.files?.[0] ?? null;
                setImageFile(file);
                if (file) setImageUrl(URL.createObjectURL(file));
              }}
            />
          </label>
          {imageUrl && <img className="recipe-form-preview" src={imageUrl} alt="Preview" />}

          {error && <p className="error">{error}</p>}

          <button type="submit" className="btn" disabled={loading}>
            {loading ? "Saving…" : isNew ? "Create recipe" : "Save changes"}
          </button>
        </form>
      </main>
    </>
  );
}
