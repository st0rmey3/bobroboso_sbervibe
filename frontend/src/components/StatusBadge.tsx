import { applicationStatusLabel, documentStatusLabel, slotStateLabel } from "../statusLabels";

export default function StatusBadge({
  status,
  kind = "document",
}: {
  status: string;
  kind?: "document" | "application" | "slot";
}) {
  const labels =
    kind === "slot" ? slotStateLabel : kind === "application" ? applicationStatusLabel : documentStatusLabel;
  return <span className={`badge badge-${status}`}>{labels[status] ?? "Состояние уточняется"}</span>;
}
