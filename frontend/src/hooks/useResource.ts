import { useCallback, useEffect, useState } from "react";
import { errorMessage } from "../api/client";

// Fetch serially, discard results after navigation, and retry interrupted polling.
export function useResource<T>(load: (signal: AbortSignal) => Promise<T>, interval = 0, shouldPoll?: (data: T) => boolean) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  const reload = useCallback(() => setRevision((value) => value + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      let repeat = interval > 0;
      try {
        const result = await load(controller.signal);
        if (controller.signal.aborted) return;
        setData(result);
        setError("");
        repeat = repeat && (!shouldPoll || shouldPoll(result));
      } catch (reason) {
        if (controller.signal.aborted) return;
        setError(errorMessage(reason));
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          if (repeat) timer = setTimeout(refresh, interval);
        }
      }
    }
    void refresh();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [load, interval, shouldPoll, revision]);
  return { data, error, loading, reload };
}
