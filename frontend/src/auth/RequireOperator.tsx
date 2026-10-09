import { useEffect, useState, type ReactNode } from "react";
import { userManager } from "./oidc";

// Cosmetic guard only — the backend checks the token on every /api/operator request.
export default function RequireOperator({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    userManager.getUser().then((user) => {
      if (user && !user.expired) setReady(true);
      else userManager.signinRedirect({ state: location.pathname });
    });
  }, []);

  return ready ? <>{children}</> : <p>Перенаправляем на вход…</p>;
}
