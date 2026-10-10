import { useCallback, useRef, useState, type FormEvent, type ReactNode } from "react";
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
  return (
    <>
      <header className="site-header">
        <Link to="/" className="brand">
          Документы<span>Приём и проверка</span>
        </Link>
        <Link to="/operator">Вход для оператора →</Link>
      </header>
      <main className="applicant-container">
        <p className="eyebrow">Оформление на работу</p>
        <h1>{appId ? "Ваш комплект документов" : "Подайте документы онлайн"}</h1>
        <p className="intro">
          Загрузите фотографии или сканы. Мы прочитаем документы и передадим их оператору на проверку.
        </p>
        {countries.error && (
          <div className="notice error" role="alert">
            {countries.error} <button onClick={countries.reload}>Повторить</button>
          </div>
        )}
        {appId ? (
          applicantToken.get(appId) ? (
            <Application key={appId} id={appId} countries={countries.data ?? []} />
          ) : (
            <div className="notice error" role="alert">
              На этом устройстве нет доступа к заявке. Откройте её в браузере, где вы подавали документы.{" "}
              <Link to="/">Подать новую заявку</Link>
            </div>
          )
        ) : countries.data ? (
          <CreateApplication countries={countries.data} onCreate={(id) => setParams({ a: id })} />
        ) : (
          countries.loading && <p role="status">Загружаем список стран…</p>
        )}
      </main>
    </>
  );
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
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: form.get("full_name"), phone: form.get("phone") || null, country }),
      });
      applicantToken.set(created.id, created.token);
      onCreate(created.id);
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel">
      <div className="section-heading">
        <span className="step">1</span>
        <h2>Расскажите о себе</h2>
      </div>
      <form onSubmit={submit}>
        <label>
          Фамилия, имя и отчество
          <input name="full_name" autoComplete="name" placeholder="Введите полное имя" required disabled={busy} />
        </label>
        <label>
          Телефон <span className="muted">необязательно</span>
          <input name="phone" type="tel" autoComplete="tel" placeholder="+7" disabled={busy} />
        </label>
        <label>
          Гражданство
          <select value={country} onChange={(event) => setCountry(event.target.value)} disabled={busy} required>
            {countries.map((item) => (
              <option key={item.code} value={item.code}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        {selected && (
          <div className="checklist-preview">
            <h3>Вам понадобятся</h3>
            <ul>
              {selected.doc_types.map((type) => (
                <li key={type.code}>{type.label}</li>
              ))}
            </ul>
            <p className="muted">Можно загрузить несколько страниц каждого документа.</p>
          </div>
        )}
        {error && (
          <p className="notice error" role="alert">
            {error}
          </p>
        )}
        <button className="primary" disabled={busy || !selected}>
          {busy ? "Создаём заявку…" : "Перейти к загрузке →"}
        </button>
      </form>
    </section>
  );
}

type SelectedUpload = {
  id: string;
  file: File;
  declaredType?: string;
  state: "selected" | "uploading" | "failed";
  error?: string;
};

function Application({ id, countries }: { id: string; countries: Country[] }) {
  const load = useCallback(
    (signal: AbortSignal) => publicApi<ApplicationPublic>(`/applications/${id}`, id, { signal }),
    [id],
  );
  const resource = useResource(load, 2000, needsPolling);
  const [uploads, setUploads] = useState<SelectedUpload[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const sending = useRef(false);
  const [receipt, setReceipt] = useState<{ accepted: number; failed: number }>();
  const app = resource.data;
  const closed = app?.status === "accepted" || app?.status === "rejected";

  function selectFiles(files: File[], declaredType?: string) {
    if (closed || sending.current) return;
    setReceipt(undefined);
    setUploads((current) => [
      ...current,
      ...files.map((file): SelectedUpload => ({ id: crypto.randomUUID(), file, declaredType, state: "selected" })),
    ]);
  }

  function removeFile(fileId: string) {
    if (sending.current) return;
    setUploads((current) => current.filter((item) => item.id !== fileId));
    setReceipt(undefined);
  }

  async function submitFiles() {
    if (closed || sending.current || !uploads.length) return;
    sending.current = true;
    setSubmitting(true);
    setReceipt(undefined);
    const batch = uploads;
    setUploads((current) => current.map((item) => ({ ...item, state: "uploading", error: undefined })));
    try {
      const results = await Promise.all(
        batch.map(async (item) => {
          const body = new FormData();
          body.set("file", item.file);
          if (item.declaredType) body.set("declared_type", item.declaredType);
          try {
            await publicApi(`/applications/${id}/documents`, id, { method: "POST", body });
            setUploads((current) => current.filter((upload) => upload.id !== item.id));
            return true;
          } catch (reason) {
            setUploads((current) =>
              current.map((upload) =>
                upload.id === item.id ? { ...upload, state: "failed", error: errorMessage(reason) } : upload,
              ),
            );
            return false;
          }
        }),
      );
      const accepted = results.filter(Boolean).length;
      setReceipt({ accepted, failed: results.length - accepted });
      resource.reload();
    } finally {
      sending.current = false;
      setSubmitting(false);
    }
  }

  if (!app)
    return resource.error ? (
      <div className="notice error" role="alert">
        {resource.error} <button onClick={resource.reload}>Повторить</button>
      </div>
    ) : (
      <p role="status">Открываем заявку…</p>
    );
  const labels = Object.fromEntries(app.slots.map((slot) => [slot.doc_type, slot.label]));
  const ready = app.slots.filter((slot) => slot.state === "ok").length;
  return (
    <>
      <section className="panel application-summary">
        <div>
          <h2>{app.full_name}</h2>
          <p className="muted">
            {countries.find((country) => country.code === app.country)?.label ?? "Гражданство указано"}
          </p>
        </div>
        <StatusBadge status={app.status} kind="application" />
        <p className="progress-caption">
          Готово {ready} из {app.slots.length} видов документов
        </p>
        <progress value={ready} max={app.slots.length || 1} />
      </section>
      {resource.error && (
        <div className="notice error" role="alert">
          {resource.error} <button onClick={resource.reload}>Повторить</button>
        </div>
      )}
      {receipt && receipt.accepted > 0 && (
        <section
          className={`notice ${receipt.failed > 0 ? "warning" : "success"}`}
          role="status"
          aria-label="Подтверждение приёма"
        >
          <h2>{receipt.failed > 0 ? "Принята часть комплекта" : "Комплект принят"}</h2>
          <p>
            Номер заявки: {id.slice(0, 8)}. Принято файлов: {receipt.accepted}.
          </p>
          <p>Разбор идёт в фоне — можно закрыть страницу и вернуться по текущей ссылке в этом браузере.</p>
          {receipt.failed > 0 && (
            <p>Не принято файлов: {receipt.failed}. Причины указаны ниже; эти файлы можно отправить повторно.</p>
          )}
        </section>
      )}
      {receipt && receipt.accepted === 0 && (
        <p className="notice error" role="alert">
          Комплект не принят. Проверьте ошибки у файлов и попробуйте ещё раз.
        </p>
      )}
      {app.missing.length > 0 && (
        <div className="notice warning">
          Не хватает: {app.missing.map((code) => labels[code] ?? "Документ").join(", ")} — пожалуйста, дошлите.
        </div>
      )}
      {needsPolling(app) && (
        <p className="muted" role="status">
          Разбор идёт в фоне. Статусы обновляются автоматически.
        </p>
      )}
      {closed && <p className="notice">Заявка рассмотрена. Загрузка новых файлов закрыта.</p>}
      {app.slots.map((slot) => (
        <UploadSlot
          key={slot.doc_type}
          slot={slot}
          documents={app.documents.filter((doc) => slot.document_ids.includes(doc.id))}
        >
          {slot.doc_type !== "unknown" && (
            <FilePicker
              label={slot.label}
              uploads={uploads.filter((item) => item.declaredType === slot.doc_type)}
              closed={closed}
              busy={submitting}
              onSelect={(files) => selectFiles(files, slot.doc_type)}
              onRemove={removeFile}
            />
          )}
        </UploadSlot>
      ))}
      {(!closed || uploads.some((item) => !item.declaredType)) && (
        <section className="panel document-slot">
          <h2>Другой документ — определим сами</h2>
          <p className="muted">
            Если документа нет в списке или вы не знаете его вид, добавьте файлы здесь. Тип определим по содержимому.
          </p>
          <FilePicker
            label="Другой документ"
            uploads={uploads.filter((item) => !item.declaredType)}
            closed={closed}
            busy={submitting}
            onSelect={(files) => selectFiles(files)}
            onRemove={removeFile}
          />
        </section>
      )}
      {!closed && (
        <section className="panel submit-documents" aria-label="Отправка комплекта">
          <h2>Отправьте выбранные файлы</h2>
          <p className="muted">
            К отправке: {uploads.length}. Выбранные файлы ещё не отправлены. До отправки оставьте страницу открытой.
          </p>
          <button className="primary" disabled={submitting || uploads.length === 0} onClick={() => void submitFiles()}>
            {submitting ? "Отправляем комплект…" : "Отправить комплект"}
          </button>
        </section>
      )}
      <p className="muted">
        Заявка сохранена в этом браузере. Вы можете вернуться по текущей ссылке и добавить документы.
      </p>
    </>
  );
}

function UploadSlot({
  slot,
  documents,
  children,
}: {
  slot: ApplicationPublic["slots"][number];
  documents: ApplicationPublic["documents"];
  children: ReactNode;
}) {
  return (
    <section className="panel document-slot">
      <div className="section-heading">
        <h2>{slot.label}</h2>
        <StatusBadge status={slot.state} kind="slot" />
      </div>
      {documents.length > 0 && (
        <ul className="file-list">
          {documents.map((doc) => (
            <li key={doc.id}>
              <div className="file-heading">
                <strong>{doc.filename}</strong>
                <StatusBadge status={doc.status} />
              </div>
              {doc.status_reason && <p className="issue">{doc.status_reason}</p>}
            </li>
          ))}
        </ul>
      )}
      {slot.missing_fields.length > 0 && <p className="issue">Не прочитано: {slot.missing_fields.join(", ")}</p>}
      {slot.warnings?.map((warning) => (
        <p className="issue" key={warning}>
          {warning}
        </p>
      ))}
      {children}
    </section>
  );
}

function FilePicker({
  label,
  uploads,
  closed,
  busy,
  onSelect,
  onRemove,
}: {
  label: string;
  uploads: SelectedUpload[];
  closed: boolean;
  busy: boolean;
  onSelect: (files: File[]) => void;
  onRemove: (fileId: string) => void;
}) {
  return (
    <>
      {uploads.length > 0 && (
        <ul className="file-list" aria-label={`Выбранные файлы: ${label}`}>
          {uploads.map((item) => (
            <li key={item.id}>
              <div className="file-heading">
                <strong>{item.file.name}</strong>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onRemove(item.id)}
                  aria-label={`Убрать файл: ${item.file.name}`}
                >
                  Убрать
                </button>
              </div>
              <p className={item.error ? "issue" : "muted"} role={item.error ? "alert" : "status"}>
                {item.error ?? (item.state === "uploading" ? "Отправляется…" : "Выбран, ещё не отправлен")}
              </p>
            </li>
          ))}
        </ul>
      )}
      {!closed && (
        <label className={`upload-button ${busy ? "disabled" : ""}`}>
          {busy ? "Загружаем файлы…" : "＋ Добавить файлы"}
          <input
            className="file-input"
            type="file"
            multiple
            accept=".pdf,.jpg,.jpeg,.png,.webp"
            aria-label={`Добавить файлы: ${label}`}
            disabled={busy}
            onChange={(event) => {
              const files = Array.from(event.target.files ?? []);
              event.target.value = "";
              if (files.length) onSelect(files);
            }}
          />
        </label>
      )}
      <p className="muted small">PDF, JPG, PNG или WEBP. Для разворотов выберите несколько файлов.</p>
    </>
  );
}
