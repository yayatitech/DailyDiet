import { Link } from "react-router-dom";

type Props = {
  text: string;
  recipeUrl?: string | null;
  recipeExternal?: boolean;
};

export default function RecipeLink({ text, recipeUrl, recipeExternal }: Props) {
  if (!recipeUrl) {
    return <span className="recipe-link-placeholder" aria-hidden="true" />;
  }

  const label = `Recipe for ${text}`;

  if (recipeExternal) {
    return (
      <a
        className="recipe-link"
        href={recipeUrl}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={label}
        title={label}
      >
        ↗
      </a>
    );
  }

  return (
    <Link className="recipe-link" to={recipeUrl} aria-label={label} title={label}>
      ↗
    </Link>
  );
}
