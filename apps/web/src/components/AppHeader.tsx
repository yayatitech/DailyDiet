import { Link } from "react-router-dom";
import { useAuth } from "../auth";

export default function AppHeader() {
  const { user, isLoggedIn, logout, loading } = useAuth();

  if (loading) {
    return <div className="auth-nav auth-nav-loading" aria-hidden="true" />;
  }

  if (isLoggedIn && user) {
    return (
      <div className="auth-nav">
        <span className="auth-email" title={user.email}>
          {user.email}
        </span>
        <button type="button" className="btn secondary auth-btn" onClick={logout}>
          Log out
        </button>
      </div>
    );
  }

  return (
    <div className="auth-nav">
      <Link to="/login" className="btn secondary auth-btn">
        Log in
      </Link>
      <Link to="/login?mode=register" className="btn auth-btn">
        Sign up
      </Link>
    </div>
  );
}
