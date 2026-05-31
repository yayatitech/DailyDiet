import { Link } from "react-router-dom";
import type { ReactNode } from "react";

type Props = {
  title: string;
  children?: ReactNode;
};

export default function RecipePageShell({ title, children }: Props) {
  return (
    <div className="recipe-page">
      <header className="recipe-page-header">
        <Link to="/" className="recipe-back-link">
          ← Meal plan
        </Link>
        <h1>{title}</h1>
        {children}
      </header>
    </div>
  );
}
