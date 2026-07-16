import axios from "axios";
import type {AxiosRequestConfig} from "axios";

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
    super(body.message ?? body.detail ?? "درخواست با خطا مواجه شد.");
    this.name = "ApiError";
    this.status = status;
    this.code = body.code ?? "API_ERROR";
    this.details = body.details ?? body;
  }
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

type RetryableRequestConfig = AxiosRequestConfig & {
  retryCount?: number;
};

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const request = error.config as RetryableRequestConfig | undefined;
    const retryCount = request?.retryCount ?? 0;
    if (
      request?.method?.toLowerCase() === "get" &&
      error.response?.status === 503 &&
      retryCount < 1
    ) {
      request.retryCount = retryCount + 1;
      return apiClient.request(request);
    }
    if (error.response) {
      throw new ApiError(error.response.status, error.response.data ?? {});
    }
    throw error;
  },
);

export function withToken(token?: string | null) {
  if (!token) return {};
  return {
    headers: {
      Authorization: `Token ${token}`,
    },
  };
}

export function unwrapList<T>(payload: unknown): T[] {
  if (Array.isArray(payload)) return payload as T[];
  if (payload && typeof payload === "object" && "results" in payload) {
    return ((payload as {results?: T[]}).results ?? []) as T[];
  }
  return [];
}
