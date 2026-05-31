type Props = {
  text: string;
  recipeUrl?: string | null;
};

export default function RecipeLink({ text, recipeUrl }: Props) {
  if (!recipeUrl) {
    return <span className="recipe-link-placeholder" aria-hidden="true" />;
  }
  return (
    <a
      className="recipe-link"
      href={recipeUrl}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`Recipe for ${text}`}
      title={`Recipe for ${text}`}
    >
      ↗
    </a>
  );
}
