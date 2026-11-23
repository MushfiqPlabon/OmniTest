import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

const rawEnvUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ?? "";
export const API_ORIGIN = rawEnvUrl.replace(/\/api\/v1\/?$/, "").replace(/\/+$/, "");

export class ApiError extends Error {
  status: number;
  code: string;
  details: Record<string, unknown>;

  constructor(status: number, message: string, code = "api_error", details: Record<string, unknown> = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

let authTokenGetter: () => string | null = () => null;
let unauthorizedHandler: () => void = () => {};

export function configureApiAuth(getToken: () => string | null, onUnauthorized: () => void): void {
  authTokenGetter = getToken;
  unauthorizedHandler = onUnauthorized;
}

export const api = createClient<paths>({ baseUrl: API_ORIGIN });

api.use({
  onRequest({ request }) {
    const token = authTokenGetter();
    if (token && !request.headers.has("Authorization")) {
      request.headers.set("Authorization", `Bearer ${token}`);
    }
    return request;
  },
});

export async function unwrap<T>(
  promise: Promise<{ data?: T; error?: unknown; response: Response }>,
  skipAutoSignout = false,
): Promise<T> {
  const { data, error, response } = await promise;
  if (response.ok) return data as T;

  if (response.status === 401 && !skipAutoSignout) {
    unauthorizedHandler();
  }
  const errObj = error as
    | { message?: string; error?: string; detail?: string; details?: Record<string, unknown> }
    | undefined;
  const msg = errObj?.message || errObj?.detail || `Request failed (${response.status})`;
  throw new ApiError(response.status, msg, errObj?.error ?? "http_error", errObj?.details ?? {});
}

export async function uploadMaterialFile(formData: FormData): Promise<components["schemas"]["MaterialResponse"]> {
  const headers = new Headers();
  const token = authTokenGetter();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_ORIGIN}/api/v1/materials/upload`, {
    method: "POST",
    headers,
    body: formData,
  });
  const body = await response.json().catch(() => ({}));
  if (response.ok) return body as components["schemas"]["MaterialResponse"];

  if (response.status === 401) unauthorizedHandler();
  throw new ApiError(response.status, body.message || body.detail || `Upload failed (${response.status})`, body.error);
}

export type Schemas = components["schemas"];
