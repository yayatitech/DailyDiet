import { FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth";
import AppHeader from "../components/AppHeader";

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, register } = useAuth();
  const registerMode = searchParams.get("mode") === "register";
  const returnTo = searchParams.get("return") || "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent, mode: "login" | "register") => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (mode === "register") {
        await register(email.trim(), password);
      } else {
        await login(email.trim(), password);
      }
      navigate(returnTo);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <header className="app-header login-page-header">
        <div className="app-header-top">
          <div className="brand">
            <Link to="/" className="brand-link">
              <h1>DailyDiet</h1>
            </Link>
            <p className="subtitle">Weekly Meal Plan · v2</p>
          </div>
          <AppHeader />
        </div>
      </header>

      <main className="login-page">
        <div className="login-card">
          <h2>{registerMode ? "Create account" : "Log in"}</h2>
          <p className="panel-hint">
            {registerMode
              ? "Sign up to save meal edits, notes, and completion tracking."
              : "Log in to save your personal meal plan and tracking."}
          </p>

          <form className="login-form" onSubmit={(e) => handleSubmit(e, registerMode ? "register" : "login")}>
            <label className="control">
              <span className="label-required">Email</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </label>
            <label className="control">
              <span className="label-required">Password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={registerMode ? "new-password" : "current-password"}
                minLength={8}
                required
              />
            </label>

            {error && <p className="error">{error}</p>}

            <button type="submit" className="btn" disabled={loading}>
              {loading ? "Please wait…" : registerMode ? "Create account" : "Log in"}
            </button>
          </form>

          <p className="login-switch">
            {registerMode ? (
              <>
                Already have an account? <Link to={`/login?return=${encodeURIComponent(returnTo)}`}>Log in</Link>
              </>
            ) : (
              <>
                New here? <Link to={`/login?mode=register&return=${encodeURIComponent(returnTo)}`}>Sign up</Link>
              </>
            )}
          </p>

          <p className="login-guest">
            <Link to="/">Continue browsing as guest</Link> (read-only template plan)
          </p>
        </div>
      </main>
    </>
  );
}
