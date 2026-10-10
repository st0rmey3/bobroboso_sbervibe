import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { operatorApi } from "../../api/client";
import type { ExpiringItem } from "../../api/types";
import DownloadButton from "../../components/DownloadButton";
import { useResource } from "../../hooks/useResource";

function remainingDays(days: number) {
  if (days < 0) return `Истёк ${Math.abs(days)} дн. назад`;
  if (days === 0) return "Истекает сегодня";
  return `Осталось ${days} дн.`;
}

function expiryDate(value: string) {
  // This is a calendar date from the server, not a timestamp in a time zone.
  const [year, month, day] = value.split("-");
  return `${day}.${month}.${year}`;
}

export default function ExpiringPage() {
  const [days, setDays] = useState(30);
  return (
    <>
      <p className="eyebrow">Контроль сроков</p>
      <h1>Истекающие документы</h1>
      <p className="intro">Документы, срок которых уже истёк или заканчивается в выбранный период.</p>
      <label className="expiry-period">
        Период проверки
        <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
          <option value={7}>Ближайшие 7 дней</option>
          <option value={30}>Ближайшие 30 дней</option>
          <option value={90}>Ближайшие 90 дней</option>
          <option value={365}>Ближайший год</option>
        </select>
      </label>
      <ExpiringResults key={days} days={days} />
    </>
  );
}

function ExpiringResults({ days }: { days: number }) {
  const load = useCallback(
    (signal: AbortSignal) => operatorApi<ExpiringItem[]>(`/expiring?days=${days}`, { signal }),
    [days],
  );
  const resource = useResource(load);
  return (
    <>
      {resource.error && (
        <div className="notice error" role="alert">
          {resource.error} <button onClick={resource.reload}>Повторить</button>
        </div>
      )}
      {resource.loading && <p role="status">Проверяем сроки документов…</p>}
      {resource.data && (
        <section className="panel table-panel">
          <div className="section-heading">
            <h2>Найдено: {resource.data.length}</h2>
            <div className="export-actions">
              <button type="button" onClick={resource.reload}>
                Обновить
              </button>
              <DownloadButton
                path={`/expiring.csv?days=${days}`}
                filename="expiring.csv"
                disabled={Boolean(resource.error)}
              >
                Скачать CSV
              </DownloadButton>
            </div>
          </div>
          {resource.data.length === 0 ? (
            <p className="empty-state">За выбранный период истекающих и просроченных документов нет.</p>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Соискатель</th>
                    <th>Документ</th>
                    <th>Поле</th>
                    <th>Дата</th>
                    <th>Срок</th>
                  </tr>
                </thead>
                <tbody>
                  {resource.data.map((item) => (
                    <tr
                      key={`${item.application_id}-${item.doc_type}-${item.field}`}
                      className={item.days_left < 0 ? "expired-row" : undefined}
                    >
                      <td>
                        <Link className="row-link" to={`/operator/applications/${item.application_id}`}>
                          {item.full_name}
                        </Link>
                      </td>
                      <td>{item.doc_label}</td>
                      <td>{item.field}</td>
                      <td>
                        <time dateTime={item.date}>{expiryDate(item.date)}</time>
                      </td>
                      <td>
                        <span className={`badge ${item.days_left < 0 ? "badge-failed" : "badge-needs_review"}`}>
                          {remainingDays(item.days_left)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </>
  );
}
