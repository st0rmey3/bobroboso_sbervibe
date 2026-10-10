export function formatDate(value: string) {
  // SQLite development timestamps have no suffix; the server stores UTC.
  const utcValue = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`;
  const date = new Date(utcValue);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}
