import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import AppHeader from "../components/AppHeader";

type Props = {
  title: string;
  children?: ReactNode;
};

export default function RecipePageShell({ title, children }: Props) {
  return (
    <>
      <header className="app-header recipe-shell-header">
        <div className="app-header-top">
          <div className="brand">
            <Link to="/" className="brand-link">
              <h1>DailyDiet</h1>
            </Link>
            <p className="subtitle">Recipes</p>
          </div>
          <AppHeader />
        </div>
      </header>
      <div className="recipe-page">
        <header className="recipe-page-header">
          <Link to="/" className="recipe-back-link">
            ← Meal plan
          </Link>
          <h1>{title}</h1>
          {children}
        </header>
      </div>
    </>
  );
}
