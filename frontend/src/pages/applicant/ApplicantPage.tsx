import { useCallback, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { applicantToken, errorMessage, publicApi } from "../../api/client";
import type { ApplicationCreated, ApplicationPublic, Country } from "../../api/types";
import StatusBadge from "../../components/StatusBadge";
import { useResource } from "../../hooks/useResource";
import { isProcessing } from "../../statusLabels";

const loadCountries = (signal: AbortSignal) => publicApi<Country[]>("/countries", undefined, { signal });
const needsPolling = (app: ApplicationPublic) => app.documents.some((doc) => isProcessing(doc.status));

export default function ApplicantPage() {
  const [params, setParams] = useSearchParams();
  const appId = params.get("a");
  const countries = useResource(loadCountries);
  return <>
    <header className="site-header"><Link to="/" className="brand">Документы<span>Приём и проверка</span></Link><Link to="/operator">Вход для оператора →</Link></header>
    <main className="applicant-container">
      <p className="eyebrow">Оформление на работу</p>
      <h1>{appId ? "Ваш комплект документов" : "Подайте документы онлайн"}</h1>
      <p className="intro">Загрузите фотографии или сканы. Мы прочитаем документы и передадим их оператору на проверку.</p>
      {countries.error && <div className="notice error" role="alert">{countries.error} <button onClick={countries.reload}>Повторить</button></div>}
      {appId ? applicantToken.get(appId) ? <Application key={appId} id={appId} countries={countries.data ?? []} /> : <div className="notice error" role="alert">На этом устройстве нет доступа к заявке. Откройте её в браузере, где вы подавали документы. <Link to="/">Подать новую заявку</Link></div> : countries.data ? <CreateApplication countries={countries.data} onCreate={(id) => setParams({ a: id })} /> : countries.loading && <p role="status">Загружаем список стран…</p>}
    </main>
  </>;
}

function CreateApplication({ countries, onCreate }: { countries: Country[]; onCreate: (id: string) => void }) {
  const [country, setCountry] = useState(countries[0]?.code ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const selected = countries.find((item) => item.code === country);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      const created = await publicApi<ApplicationCreated>("/applications", undefined, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: form.get("full_name"), phone: form.get("phone") || null, country }),
      });
      applicantToken.set(created.id, created.token);
      onCreate(created.id);
    } catch (reason) { setError(errorMessage(reason)); }
    finally { setBusy(false); }
  }
  return <section className="panel">
    <div className="section-heading"><span className="step">1</span><h2>Расскажите о себе</h2></div>
    <form onSubmit={submit}>
      <label>Фамилия, имя и отчество<input name="full_name" autoComplete="name" placeholder="Введите полное имя" required disabled={busy} /></label>
      <label>Телефон <span className="muted">необязательно</span><input name="phone" type="tel" autoComplete="tel" placeholder="+7" disabled={busy} /></label>
      <label>Гражданство<select value={country} onChange={(event) => setCountry(event.target.value)} disabled={busy} required>{countries.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}</select></label>
      {selected && <div className="checklist-preview"><h3>Вам понадобятся</h3><ul>{selected.doc_types.map((type) => <li key={type.code}>{type.label}</li>)}</ul><p className="muted">Можно загрузить несколько страниц каждого документа.</p></div>}
      {error && <p className="notice error" role="alert">{error}</p>}
      <button className="primary" disabled={busy || !selected}>{busy ? "Создаём заявку…" : "Перейти к загрузке →"}</button>
    </form>
  </section>;
}

function Application({ id, countries }: { id: string; countries: Country[] }) {
  const load = useCallback((signal: AbortSignal) => publicApi<ApplicationPublic>(`/applications/${id}`, id, { signal }), [id]);
  const resource = useResource(load, 2000, needsPolling);
  const [accepted, setAccepted] = useState(0);
  const app = resource.data;
  if (!app) return resource.error ? <div className="notice error" role="alert">{resource.error} <button onClick={resource.reload}>Повторить</button></div> : <p role="status">Открываем заявку…</p>;
  const closed = app.status === "accepted" || app.status === "rejected";
  const labels = Object.fromEntries(app.slots.map((slot) => [slot.doc_type, slot.label]));
  const ready = app.slots.filter((slot) => slot.state === "ok").length;
  return <>
    <section className="panel application-summary"><div><h2>{app.full_name}</h2><p className="muted">{countries.find((country) => country.code === app.country)?.label ?? "Гражданство указано"}</p></div><StatusBadge status={app.status} kind="application" /><p className="progress-caption">Готово {ready} из {app.slots.length} видов документов</p><progress value={ready} max={app.slots.length || 1} /></section>
    {resource.error && <div className="notice error" role="alert">{resource.error} <button onClick={resource.reload}>Повторить</button></div>}
    {accepted > 0 && <p className="notice success" role="status">Принято файлов: {accepted}. Документы поставлены на разбор — страницу можно не обновлять.</p>}
    {app.missing.length > 0 && <div className="notice warning">Не хватает: {app.missing.map((code) => labels[code] ?? "Документ").join(", ")} — пожалуйста, дошлите.</div>}
    {needsPolling(app) && <p className="muted" role="status">Разбор идёт в фоне. Статусы обновляются автоматически.</p>}
    {closed && <p className="notice">Заявка рассмотрена. Загрузка новых файлов закрыта.</p>}
    {app.slots.map((slot) => <UploadSlot key={slot.doc_type} id={id} slot={slot} documents={app.documents.filter((doc) => slot.document_ids.includes(doc.id))} closed={closed} onUploaded={(count) => { setAccepted((value) => value + count); resource.reload(); }} />)}
    <p className="muted">Заявка сохранена в этом браузере. Вы можете вернуться по текущей ссылке и добавить документы.</p>
  </>;
}

function UploadSlot({ id, slot, documents, closed, onUploaded }: { id: string; slot: ApplicationPublic["slots"][number]; documents: ApplicationPublic["documents"]; closed: boolean; onUploaded: (count: number) => void }) {
  const [uploads, setUploads] = useState<{ name: string; error?: string; pending: boolean }[]>([]);
  const busy = uploads.some((upload) => upload.pending);
  async function upload(files: File[]) {
    setUploads(files.map((file) => ({ name: file.name, pending: true })));
    await Promise.all(files.map(async (file, index) => {
      const body = new FormData(); body.set("file", file); body.set("declared_type", slot.doc_type);
      let error: string | undefined;
      try { await publicApi(`/applications/${id}/documents`, id, { method: "POST", body }); onUploaded(1); }
      catch (reason) { error = errorMessage(reason); }
      setUploads((current) => current.map((item, position) => position === index ? { ...item, pending: false, error } : item));
    }));
  }
  return <section className="panel document-slot">
    <div className="section-heading"><h2>{slot.label}</h2><StatusBadge status={slot.state} kind="slot" /></div>
    {documents.length > 0 && <ul className="file-list">{documents.map((doc) => <li key={doc.id}><div className="file-heading"><strong>{doc.filename}</strong><StatusBadge status={doc.status} /></div>{doc.status_reason && <p className="issue">{doc.status_reason}</p>}</li>)}</ul>}
    {slot.missing_fields.length > 0 && <p className="issue">Не прочитано: {slot.missing_fields.join(", ")}</p>}
    {slot.warnings?.map((warning) => <p className="issue" key={warning}>{warning}</p>)}
    {uploads.filter((item) => item.pending || item.error).map((item, index) => <p key={index} className={item.error ? "issue" : "muted"} role={item.error ? "alert" : "status"}>{item.name}: {item.error ?? "Загружается…"}</p>)}
    {!closed && <label className={`upload-button ${busy ? "disabled" : ""}`}>{busy ? "Загружаем файлы…" : "＋ Добавить файлы"}<input className="file-input" type="file" multiple accept=".pdf,.jpg,.jpeg,.png" aria-label={`Добавить файлы: ${slot.label}`} disabled={busy} onChange={(event) => { const files = Array.from(event.target.files ?? []); event.target.value = ""; if (files.length) void upload(files); }} /></label>}
    <p className="muted small">PDF, JPG или PNG. Для разворотов выберите несколько файлов.</p>
  </section>;
}
