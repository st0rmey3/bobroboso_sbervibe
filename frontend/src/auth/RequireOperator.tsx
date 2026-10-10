import { useEffect, useRef, useState, type ReactNode } from "react";
import { userManager } from "./oidc";

// Cosmetic guard only — the backend checks the token on every /api/operator request.
export default function RequireOperator({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(false);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    userManager.getUser().then((user) => {
      if (user && !user.expired) setReady(true);
      else return userManager.signinRedirect({ state: location.pathname + location.search });
    }).catch(() => setError(true));
  }, []);

  if (error) return <main className="applicant-container"><h1>Не удалось открыть страницу входа</h1><p>Проверьте соединение и доступность сервиса входа.</p><button onClick={() => location.reload()}>Повторить вход</button></main>;
  return ready ? <>{children}</> : <p>Перенаправляем на вход…</p>;
}
