import { accessToken } from "../auth/oidc";

// Thin fetch wrapper. Types: run `npm run gen:api` → src/api/schema.d.ts (generated from docs/api/openapi.json).

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export function errorMessage(reason: unknown): string {
  return reason instanceof ApiError ? reason.message : "Не удалось связаться с сервером. Попробуйте ещё раз.";
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    // backend returns Russian, user-facing messages in `detail`
    const detail = typeof body?.detail === "string" ? body.detail : "Не удалось выполнить запрос. Проверьте данные и попробуйте ещё раз.";
    throw new ApiError(res.status, detail);
  }
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
export async function operatorApi<T>(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  const token = await accessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return request<T>(`/api/operator${path}`, { ...init, headers });
}

// Files need the bearer header too, so <img src> can't point at the API directly: fetch → object URL.
export async function operatorFileUrl(docId: string): Promise<string> {
  const token = await accessToken();
  const res = await fetch(`/api/operator/documents/${docId}/file`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new ApiError(res.status, "Не удалось открыть файл");
  return URL.createObjectURL(await res.blob());
}
