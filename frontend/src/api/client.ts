export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export type ApiErrorBody = {
  code: string;
  message: string;
  details: unknown;
};

export class ApiError extends Error {
  status: number;
  code: string;
  details: unknown;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.code;
    this.details = body.details;
  }
}

const RETRYABLE_STATUSES = new Set([408, 429, 500, 502, 503, 504]);
const RETRY_DELAY_MS = 350;

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function requestMethod(options: RequestInit) {
  return (options.method ?? "GET").toUpperCase();
}

function canRetry(method: string, response?: Response) {
  if (method !== "GET") return false;
  if (!response) return true;
  return RETRYABLE_STATUSES.has(response.status);
}

async function readErrorBody(response: Response): Promise<ApiErrorBody> {
  try {
    const body = await response.json();
    return {
      code: body.code ?? "API_ERROR",
      message: body.message ?? body.detail ?? "Request failed.",
      details: body.details ?? body,
    };
  } catch {
    return {
      code: "API_ERROR",
      message: `Request failed with status ${response.status}.`,
      details: {},
    };
  }
}

export async function apiFetch(path: string, options: RequestInit = {}, token?: string) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };

  if (token) headers.Authorization = `Token ${token}`;

  const method = requestMethod(options);
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {...options, headers});
  } catch (exc) {
    if (!canRetry(method)) throw exc;
    await delay(RETRY_DELAY_MS);
    response = await fetch(`${API_BASE_URL}${path}`, {...options, headers});
  }

  if (!response.ok && canRetry(method, response)) {
    await delay(RETRY_DELAY_MS);
    response = await fetch(`${API_BASE_URL}${path}`, {...options, headers});
  }

  if (!response.ok) {
    const body = await readErrorBody(response);
    throw new ApiError(response.status, body);
  }

  if (response.status === 204) return null;

  return response.json();
}

export function unwrapList<T>(payload: unknown): T[] {
  if (Array.isArray(payload)) return payload as T[];
  if (payload && typeof payload === "object" && "results" in payload) {
    return ((payload as {results?: T[]}).results ?? []) as T[];
  }
  return [];
}
