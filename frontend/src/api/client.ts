import { accessToken } from "../auth/oidc";

// Thin fetch wrapper. Types: run `npm run gen:api` → src/api/schema.d.ts (generated from docs/api/openapi.json).

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export function errorMessage(reason: unknown): string {
  return reason instanceof ApiError ? reason.message : "Не удалось связаться с сервером. Попробуйте ещё раз.";
}

async function checkedResponse(path: string, init: RequestInit = {}): Promise<Response> {
  const res = await fetch(path, init);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    // backend returns Russian, user-facing messages in `detail`
    const detail =
      typeof body?.detail === "string"
        ? body.detail
        : "Не удалось выполнить запрос. Проверьте данные и попробуйте ещё раз.";
    throw new ApiError(res.status, detail);
  }
  return res;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await checkedResponse(path, init);
  return res.status === 204 ? (undefined as T) : res.json();
}

// --- applicant: token per application is kept in localStorage ---
export const applicantToken = {
  get: (appId: string) => localStorage.getItem(`app-token:${appId}`),
  set: (appId: string, token: string) => localStorage.setItem(`app-token:${appId}`, token),
};

export function publicApi<T>(path: string, appId?: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  const token = appId ? applicantToken.get(appId) : null;
  if (token) headers.set("X-Application-Token", token);
  return request<T>(`/api/public${path}`, { ...init, headers });
}

// --- operator: bearer token from Keycloak ---
async function operatorResponse(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  const token = await accessToken();
  if (!token) throw new ApiError(401, "Сеанс завершён. Войдите в рабочее место оператора ещё раз.");
  headers.set("Authorization", `Bearer ${token}`);
  return checkedResponse(`/api/operator${path}`, { ...init, headers });
}

export async function operatorApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await operatorResponse(path, init);
  return res.status === 204 ? (undefined as T) : res.json();
}

// Files need the bearer header too, so <img src> can't point at the API directly: fetch → object URL.
export async function operatorFileUrl(docId: string): Promise<string> {
  const res = await operatorResponse(`/documents/${docId}/file`);
  return URL.createObjectURL(await res.blob());
}

function downloadFilename(disposition: string | null, fallback: string): string {
  const encoded = disposition?.match(/filename\*\s*=\s*UTF-8'[^']*'([^;]+)/i)?.[1];
  const plain = disposition?.match(/filename\s*=\s*"([^"]+)"/i)?.[1];
  let name = plain || fallback;
  if (encoded) {
    try {
      name = decodeURIComponent(encoded.trim());
    } catch {
      /* Use the plain filename if the extended parameter is malformed. */
    }
  }
  return name.replace(/[<>:"/\\|?*\u0000-\u001f\u007f]/g, "_").replace(/[. ]+$/, "") || fallback;
}

export async function operatorDownload(path: string, fallbackFilename: string): Promise<void> {
  const res = await operatorResponse(path);
  if (res.headers.get("Content-Type")?.split(";")[0].trim().toLowerCase() !== "text/csv") {
    throw new ApiError(502, "Сервер не вернул CSV-файл. Попробуйте скачать ещё раз.");
  }
  // Preserve the server's UTF-8 BOM and formula escaping byte for byte.
  const url = URL.createObjectURL(await res.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = downloadFilename(res.headers.get("Content-Disposition"), fallbackFilename);
  link.hidden = true;
  document.body.appendChild(link);
  try {
    link.click();
  } finally {
    link.remove();
    // Give the browser time to consume the URL before releasing the blob.
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}
