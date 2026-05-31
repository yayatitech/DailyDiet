import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import App from "./App";
import RecipeEditPage from "./pages/RecipeEditPage";
import RecipeListPage from "./pages/RecipeListPage";
import RecipeViewPage from "./pages/RecipeViewPage";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/recipes" element={<RecipeListPage />} />
        <Route path="/recipes/new" element={<RecipeEditPage />} />
        <Route path="/recipes/:id" element={<RecipeViewPage />} />
        <Route path="/recipes/:id/edit" element={<RecipeEditPage />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>
);
