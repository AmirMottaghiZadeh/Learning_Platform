import axios, { AxiosRequestConfig } from "axios";

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export type ApiErrorBody = {
  code?: string;
  message?: string;
  detail?: string;
  details?: unknown;
};

export class ApiError extends Error {
  status: number;
  code: string;
  details: unknown;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message ?? body.detail ?? "Request failed.");
    this.name = "ApiError";
    this.status = status;
    this.code = body.code ?? "API_ERROR";
    this.details = body.details ?? body;
  }
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

type RetryableConfig = AxiosRequestConfig & {
  authRetry?: boolean;
  retryCount?: number;
  skipAuth?: boolean;
};

type AuthController = {
  getAccessToken: () => string | null;
  refreshAccessToken: () => Promise<string>;
  onAuthFailed: () => void | Promise<void>;
};

let auth: AuthController | null = null;
let refreshPromise: Promise<string> | null = null;

export function configureAuth(controller: AuthController | null) {
  auth = controller;
  refreshPromise = null;
}

apiClient.interceptors.request.use((request) => {
  const token = auth?.getAccessToken();
  if (token && !(request as RetryableConfig).skipAuth) {
    request.headers.set("Authorization", `Bearer ${token}`);
  }
  return request;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const request = error.config as RetryableConfig | undefined;

    // A locked feature answers 503; retry a GET once in case it was a blip.
    const retryCount = request?.retryCount ?? 0;
    if (
      request?.method?.toLowerCase() === "get" &&
      error.response?.status === 503 &&
      retryCount < 1
    ) {
      request.retryCount = retryCount + 1;
      return apiClient.request(request);
    }

    if (
      request &&
      error.response?.status === 401 &&
      !request.authRetry &&
      !request.skipAuth &&
      auth
    ) {
      request.authRetry = true;
      try {
        refreshPromise ??= auth.refreshAccessToken();
        const token = await refreshPromise;
        request.headers = { ...request.headers, Authorization: `Bearer ${token}` };
        return await apiClient.request(request);
      } catch (refreshError) {
        await auth.onAuthFailed();
        throw refreshError;
      } finally {
        refreshPromise = null;
      }
    }

    if (request?.authRetry && error.response?.status === 401 && auth) {
      await auth.onAuthFailed();
    }

    if (error.response) {
      throw new ApiError(error.response.status, error.response.data ?? {});
    }
    throw error;
  },
);

export function unwrapList<T>(payload: unknown): T[] {
  if (Array.isArray(payload)) return payload as T[];
  if (payload && typeof payload === "object" && "results" in payload) {
    return ((payload as { results?: T[] }).results ?? []) as T[];
  }
  return [];
}
