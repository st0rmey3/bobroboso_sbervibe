import { useCallback, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { operatorApi } from "../../api/client";
import type { ApplicationListItem, Country } from "../../api/types";
import StatusBadge from "../../components/StatusBadge";
import { useResource } from "../../hooks/useResource";
import { applicationStatusLabel } from "../../statusLabels";
import { formatDate } from "./format";

export default function ApplicationList({ countries }: { countries: Country[] }) {
  const [query, setQuery] = useState("");
  const load = useCallback((signal: AbortSignal) => operatorApi<ApplicationListItem[]>(`/applications${query ? `?${query}` : ""}`, { signal }), [query]);
  const resource = useResource(load, 5000);
  function filter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const params = new URLSearchParams();
    for (const key of ["q", "country", "status"]) { const value = String(form.get(key) ?? "").trim(); if (value) params.set(key, value); }
    setQuery(params.toString());
    resource.reload();
  }
  return <>
    <p className="eyebrow">Рабочее место</p><h1>Заявки соискателей</h1><p className="intro">Найдите заявку и сверьте распознанные данные с оригиналами.</p>
    <form className="panel filters" onSubmit={filter}>
      <label>Поиск по имени<input name="q" type="search" placeholder="Фамилия или имя" /></label>
      <label>Гражданство<select name="country"><option value="">Все страны</option>{countries.map((country) => <option key={country.code} value={country.code}>{country.label}</option>)}</select></label>
      <label>Состояние<select name="status"><option value="">Все состояния</option>{Object.entries(applicationStatusLabel).map(([code, label]) => <option key={code} value={code}>{label}</option>)}</select></label>
      <button className="primary">Найти</button><button type="reset" onClick={() => { setQuery(""); resource.reload(); }}>Сбросить</button>
    </form>
    {resource.error && <div className="notice error" role="alert">{resource.error} <button onClick={resource.reload}>Повторить</button></div>}
    {resource.loading && <p role="status">Загружаем заявки…</p>}
    {resource.data && <section className="panel table-panel"><div className="section-heading"><h2>Найдено: {resource.data.length}</h2><span className="muted small">Обновляется автоматически</span></div>
      {resource.data.length === 0 ? <p className="empty-state">Заявок по выбранным условиям пока нет.</p> : <div className="table-scroll"><table><thead><tr><th>Соискатель</th><th>Гражданство</th><th>Состояние</th><th>Готово файлов</th><th>Внимание</th><th>Поступила</th></tr></thead><tbody>{resource.data.map((app) => <tr key={app.id}>
        <td><Link className="row-link" to={`/operator/applications/${app.id}`}>{app.full_name}</Link></td><td>{countries.find((country) => country.code === app.country)?.label ?? "—"}</td><td><StatusBadge status={app.status} kind="application" /></td><td>{app.documents_done} / {app.documents_total}</td><td>{app.documents_attention > 0 ? <strong className="issue">{app.documents_attention}</strong> : "—"}</td><td>{formatDate(app.created_at)}</td>
      </tr>)}</tbody></table></div>}
    </section>}
  </>;
}
