import { Link } from "react-router-dom";
import { operatorApi } from "../../api/client";
import type { ProcessingItem, QueueStats } from "../../api/types";
import StatusBadge from "../../components/StatusBadge";
import { useResource } from "../../hooks/useResource";
import { formatDate } from "./format";

async function loadProcessing(signal: AbortSignal) {
  const [items, stats] = await Promise.all([
    operatorApi<ProcessingItem[]>("/processing", { signal }),
    operatorApi<QueueStats>("/stats", { signal }),
  ]);
  return { items, stats };
}

export default function ProcessingPage() {
  const resource = useResource(loadProcessing, 2000);
  return (
    <>
      <p className="eyebrow">Фоновый разбор</p>
      <h1>Документы в работе</h1>
      <p className="intro">Очередь обновляется каждые две секунды.</p>
      {resource.error && (
        <div className="notice error" role="alert">
          {resource.error} <button onClick={resource.reload}>Повторить</button>
        </div>
      )}
      {!resource.data && resource.loading && <p role="status">Загружаем очередь…</p>}
      {resource.data && (
        <>
          <div className="stats-grid">
            {[
              ["Ждут разбора", resource.data.stats.queued],
              ["Разбираются", resource.data.stats.running],
              ["Завершено", resource.data.stats.done],
              ["Ошибки", resource.data.stats.failed],
              [
                "Среднее время",
                resource.data.stats.avg_processing_ms == null
                  ? "—"
                  : `${(resource.data.stats.avg_processing_ms / 1000).toFixed(1)} с`,
              ],
            ].map(([label, value]) => (
              <section className="panel stat" key={label}>
                <span className="muted">{label}</span>
                <strong>{value}</strong>
              </section>
            ))}
          </div>
          <section className="panel table-panel">
            <h2>Текущие документы</h2>
            {resource.data.items.length === 0 ? (
              <p className="empty-state">Сейчас нет документов в очереди или в обработке.</p>
            ) : (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Файл / соискатель</th>
                      <th>Состояние</th>
                      <th>Попытки</th>
                      <th>Принят</th>
                      <th>Причина</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resource.data.items.map((item) => (
                      <tr key={item.document_id}>
                        <td>
                          <strong className="filename">{item.filename}</strong>
                          <Link to={`/operator/applications/${item.application_id}`}>{item.full_name}</Link>
                        </td>
                        <td>
                          <StatusBadge status={item.status} />
                        </td>
                        <td>{item.attempts}</td>
                        <td>{formatDate(item.created_at)}</td>
                        <td className="issue">{item.last_error || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </>
  );
}
