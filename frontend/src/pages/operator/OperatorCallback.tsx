import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { userManager } from "../../auth/oidc";

export default function OperatorCallback() {
  const navigate = useNavigate();
  useEffect(() => {
    userManager
      .signinRedirectCallback()
      .then((user) => navigate((user.state as string) || "/operator", { replace: true }))
      .catch(() => navigate("/operator", { replace: true }));
  }, [navigate]);
  return <p>Входим…</p>;
}
