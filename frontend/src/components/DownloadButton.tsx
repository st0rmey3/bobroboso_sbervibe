import { useState, type ReactNode } from "react";
import { errorMessage, operatorDownload } from "../api/client";

export default function DownloadButton({
  path,
  filename,
  children,
  disabled = false,
  onDownloaded,
}: {
  path: string;
  filename: string;
  children: ReactNode;
  disabled?: boolean;
  onDownloaded?: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function download() {
    setBusy(true);
    setError("");
    try {
      await operatorDownload(path, filename);
      onDownloaded?.();
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="download-control">
      <button type="button" disabled={disabled || busy} onClick={download}>
        {busy ? "Готовим файл…" : children}
      </button>
      {error && (
        <p className="issue small" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
