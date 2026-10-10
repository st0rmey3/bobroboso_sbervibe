import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { errorMessage, operatorApi, operatorFileUrl } from "../../api/client";
import type { ApplicationOperator, Country, DocumentOperator, MergedField, SlotOperator } from "../../api/types";
import StatusBadge from "../../components/StatusBadge";
import { useResource } from "../../hooks/useResource";
import { isProcessing } from "../../statusLabels";
import { formatDate } from "./format";

const needsPolling = (app: ApplicationOperator) => app.documents.some((doc) => isProcessing(doc.status));

export default function ApplicationCard({ countries }: { countries: Country[] }) {
  const { id } = useParams();
  return <Card key={id} id={id!} countries={countries} />;
}

function Card({ id, countries }: { id: string; countries: Country[] }) {
  const load = useCallback((signal: AbortSignal) => operatorApi<ApplicationOperator>(`/applications/${id}`, { signal }), [id]);
  const resource = useResource(load, 3000, needsPolling);
  const app = resource.data;
  const types = countries.flatMap((country) => country.doc_types);
  return <>
    <Link className="back-link" to="/operator">← Все заявки</Link>
    {resource.error && <div className="notice error" role="alert">{resource.error} <button onClick={resource.reload}>Повторить</button></div>}
    {!app && resource.loading && <p role="status">Открываем заявку…</p>}
    {app && <>
      <div className="card-heading"><div><p className="eyebrow">Карточка соискателя</p><h1>{app.full_name}</h1><p className="muted">{countries.find((country) => country.code === app.country)?.label ?? "—"} · {app.phone || "Телефон не указан"} · {formatDate(app.created_at)}</p></div><StatusBadge status={app.status} kind="application" /></div>
      {app.missing.length > 0 && <p className="notice warning">Не хватает: {app.missing.map((code) => app.slots.find((slot) => slot.doc_type === code)?.label ?? "Документ").join(", ")}</p>}
      {app.slots.map((slot) => <Slot key={slot.doc_type} slot={slot} documents={app.documents.filter((doc) => slot.document_ids.includes(doc.id))} specs={types.find((type) => type.code === slot.doc_type)?.fields ?? []} onChanged={resource.reload} />)}
      <section className="panel"><h2>История заявки</h2>{app.history.length === 0 ? <p className="muted">Событий пока нет.</p> : <ol className="history">{app.history.map((event, index) => <li key={`${event.created_at}-${index}`}><div><strong>{actionLabel(event.action)}</strong><span className="muted small">{formatDate(event.created_at)} · {actorLabel(event.actor)}</span></div><HistoryData event={event} types={types} /></li>)}</ol>}</section>
    </>}
  </>;
}

function Slot({ slot, documents, specs, onChanged }: { slot: SlotOperator; documents: DocumentOperator[]; specs: Country["doc_types"][number]["fields"]; onChanged: () => void }) {
  const fieldNames = Array.from(new Set([...specs.map((spec) => spec.name), ...Object.keys(slot.fields)]));
  const fallback = documents.find((doc) => (doc.detected_type ?? doc.declared_type) === slot.doc_type);
  return <section className="panel review-slot">
    <div className="section-heading"><h2>{slot.label}</h2><StatusBadge status={slot.state} kind="slot" /></div>
    {slot.warnings?.map((warning) => <p className="notice warning" key={warning}>{warning}</p>)}
    {slot.missing_fields.length > 0 && <p className="issue">Не прочитано: {slot.missing_fields.join(", ")}</p>}
    <div className="review-grid"><div className="originals"><h3>Оригиналы</h3>{documents.length === 0 ? <p className="empty-state">Соискатель ещё не загрузил файлы.</p> : documents.map((doc) => <Original key={doc.id} doc={doc} onChanged={onChanged} />)}</div>
      <div className="recognized"><h3>Распознанные данные</h3><p className="muted small">Перепроверьте выделенные поля. Правки сохраняются по одному полю.</p>{fieldNames.length === 0 && <p className="muted">Данные появятся после разбора документа.</p>}{fieldNames.map((name) => {
        const field: MergedField = slot.fields[name] ?? { value: null, confidence: 0, issues: [], edited_by: null, document_id: null };
        const source = documents.find((doc) => doc.id === field.document_id) ?? fallback;
        return <FieldEditor key={`${name}-${source?.id ?? "missing"}`} name={name} label={specs.find((spec) => spec.name === name)?.label ?? "Поле документа"} field={field} documentId={source?.id} disabled={!source || isProcessing(source.status)} onChanged={onChanged} />;
      })}</div>
    </div>
  </section>;
}

function FieldEditor({ name, label, field, documentId, disabled, onChanged }: { name: string; label: string; field: MergedField; documentId?: string; disabled: boolean; onChanged: () => void }) {
  const [draft, setDraft] = useState<string>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const value = draft ?? field.value ?? "";
  const dirty = draft !== undefined && draft !== (field.value ?? "");
  async function save(event: FormEvent) {
    event.preventDefault();
    if (!documentId || !dirty) return;
    setBusy(true); setError(""); setSaved(false);
    try {
      const updated = await operatorApi<DocumentOperator>(`/documents/${documentId}/fields`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ fields: { [name]: value.trim() || null } }) });
      setDraft(updated.fields[name]?.value ?? ""); setSaved(true); onChanged();
    } catch (reason) { setError(errorMessage(reason)); }
    finally { setBusy(false); }
  }
  // Adopt the saved server value while preserving any newer unsaved change.
  useEffect(() => { if (draft !== undefined && draft === (field.value ?? "")) setDraft(undefined); }, [field.value, draft]);
  return <form className={`field-editor ${field.confidence < 0.6 || field.issues.length ? "field-attention" : ""}`} onSubmit={save}>
    <label>{label}<input value={value} disabled={disabled || busy} onChange={(event) => { setDraft(event.target.value); setSaved(false); }} /></label>
    <div className="field-meta"><span className="muted small">Уверенность: {Math.round(field.confidence * 100)}%</span>{field.edited_by && <span className="edited-badge">Правка оператора: {field.edited_by}</span>}</div>
    {field.issues.map((issue) => <p className="issue small" key={issue}>{issue}</p>)}
    {error && <p className="issue" role="alert">{error}</p>}{saved && <span className="save-status" role="status">Сохранено</span>}
    {dirty && <div className="field-actions"><button className="primary" disabled={disabled || busy}>{busy ? "Сохраняем…" : "Сохранить"}</button><button type="button" disabled={busy} onClick={() => { setDraft(undefined); setError(""); }}>Отменить</button></div>}
  </form>;
}

function Original({ doc, onChanged }: { doc: DocumentOperator; onChanged: () => void }) {
  const [url, setUrl] = useState("");
  const [fileError, setFileError] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [zoom, setZoom] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    let objectUrl: string;
    operatorFileUrl(doc.id).then((result) => {
      objectUrl = result;
      if (active) { setUrl(result); setFileError(""); } else URL.revokeObjectURL(result);
    }).catch((reason) => { if (active) setFileError(errorMessage(reason)); });
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [doc.id, attempt]);
  async function reprocess() {
    setBusy(true); setError("");
    try { await operatorApi(`/documents/${doc.id}/reprocess`, { method: "POST" }); onChanged(); }
    catch (reason) { setError(errorMessage(reason)); }
    finally { setBusy(false); }
  }
  return <article className="original-file"><div className="file-heading"><strong>{doc.filename}</strong><StatusBadge status={doc.status} /></div>
    {doc.status_reason && <p className="issue">{doc.status_reason}</p>}
    {fileError ? <p className="issue" role="alert">{fileError} <button onClick={() => setAttempt((value) => value + 1)}>Повторить</button></p> : !url ? <p role="status">Открываем оригинал…</p> : doc.mime === "application/pdf" ? <><iframe className="pdf-preview" src={url} title={`Оригинал: ${doc.filename}`} /><a href={url} target="_blank" rel="noreferrer">Открыть PDF крупнее ↗</a></> : <button className="image-preview" onClick={() => setZoom(true)} aria-label={`Увеличить: ${doc.filename}`}><img src={url} alt={`Оригинал: ${doc.filename}`} /><span>Нажмите, чтобы увеличить</span></button>}
    {zoom && <Zoom url={url} filename={doc.filename} onClose={() => setZoom(false)} />}
    {error && <p className="issue" role="alert">{error}</p>}
    <button disabled={busy || isProcessing(doc.status)} onClick={reprocess}>{busy ? "Отправляем…" : "Разобрать заново"}</button>
    {doc.ocr_text && <details><summary>Что прочитала модель</summary><pre className="ocr-text">{doc.ocr_text}</pre></details>}
  </article>;
}

function Zoom({ url, filename, onClose }: { url: string; filename: string; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => { dialog.current?.showModal(); }, []);
  return <dialog ref={dialog} className="zoom-dialog" onCancel={onClose}><div className="section-heading"><strong>{filename}</strong><button onClick={onClose}>Закрыть</button></div><img src={url} alt={filename} /></dialog>;
}

const actions: Record<string, string> = { application_created: "Заявка создана", document_uploaded: "Файл загружен", upload_rejected: "Загрузка отклонена", fields_edited: "Поля исправлены", reprocess_requested: "Запрошен повторный разбор", document_processed: "Разбор документа завершён", document_done: "Документ разобран", document_failed: "Ошибка разбора", processing_started: "Разбор начат", processing_finished: "Разбор завершён" };
function actionLabel(action: string) { return actions[action] ?? "Обновление заявки"; }
function actorLabel(actor: string) { return actor === "applicant" ? "Соискатель" : actor === "system" || actor === "worker" ? "Система" : actor.startsWith("operator:") ? `Оператор ${actor.slice(9)}` : "Система"; }

function HistoryData({ event, types }: { event: ApplicationOperator["history"][number]; types: Country["doc_types"] }) {
  const data = event.data as Record<string, unknown>;
  const changes = data.changes;
  return <>{typeof data.filename === "string" && <p>{data.filename}</p>}{typeof data.reason === "string" && <p className="issue">{data.reason}</p>}{changes && typeof changes === "object" && <ul>{Object.entries(changes).map(([name, change]) => {
    const values = change as { old?: unknown; new?: unknown };
    const label = types.flatMap((type) => type.fields).find((field) => field.name === name)?.label ?? "Поле документа";
    return <li key={name}>{label}: {String(values.old ?? "не заполнено")} → {String(values.new ?? "не заполнено")}</li>;
  })}</ul>}</>;
}
