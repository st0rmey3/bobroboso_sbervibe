import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { userManager } from "../../auth/oidc";

// StrictMode mounts effects twice; an authorization code may only be exchanged once.
let callback: ReturnType<typeof userManager.signinRedirectCallback> | undefined;

export default function OperatorCallback() {
  const navigate = useNavigate();
  const [error, setError] = useState(false);
  useEffect(() => {
    callback ??= userManager.signinRedirectCallback();
    callback
      .then((user) => {
        const destination =
          typeof user.state === "string" &&
          user.state.startsWith("/operator/") &&
          !user.state.startsWith("/operator/callback")
            ? user.state
            : "/operator";
        navigate(destination, { replace: true });
      })
      .catch(() => setError(true));
  }, [navigate]);
  if (error)
    return (
      <main className="applicant-container">
        <h1>Не удалось завершить вход</h1>
        <p>Попробуйте войти ещё раз.</p>
        <Link to="/operator">Вернуться к входу</Link>
      </main>
    );
  return <p>Входим…</p>;
}
