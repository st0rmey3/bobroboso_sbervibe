import { useState } from "react";
import { Link, NavLink, Route, Routes } from "react-router-dom";
import { errorMessage, publicApi } from "../../api/client";
import type { Country } from "../../api/types";
import { userManager } from "../../auth/oidc";
import { useResource } from "../../hooks/useResource";
import ApplicationList from "./ApplicationList";
import ApplicationCard from "./ApplicationCard";
import ProcessingPage from "./ProcessingPage";

const loadCountries = (signal: AbortSignal) => publicApi<Country[]>("/countries", undefined, { signal });

export default function OperatorPage() {
  const countries = useResource(loadCountries);
  const [error, setError] = useState("");
  return <>
    <header className="site-header operator-header"><Link to="/operator" className="brand">Документы<span>Рабочее место оператора</span></Link><nav aria-label="Разделы оператора"><NavLink to="/operator" end>Заявки</NavLink><NavLink to="/operator/processing">В работе</NavLink></nav><button onClick={() => userManager.signoutRedirect().catch((reason) => setError(errorMessage(reason)))}>Выйти</button></header>
    <main className="operator-container">
      {(error || countries.error) && <div className="notice error" role="alert">{error || countries.error} <button onClick={countries.reload}>Повторить</button></div>}
      <Routes>
        <Route index element={<ApplicationList countries={countries.data ?? []} />} />
        <Route path="applications/:id" element={<ApplicationCard countries={countries.data ?? []} />} />
        <Route path="processing" element={<ProcessingPage />} />
        <Route path="*" element={<p>Страница не найдена. <Link to="/operator">Вернуться к заявкам</Link></p>} />
      </Routes>
    </main>
  </>;
}
