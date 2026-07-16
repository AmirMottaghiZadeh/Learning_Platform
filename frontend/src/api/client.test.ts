import type {AxiosAdapter, InternalAxiosRequestConfig} from "axios";

import {ApiError, apiClient, unwrapList} from "./client";

type AdapterResponse = {
  data: unknown;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  config: InternalAxiosRequestConfig;
};

const originalAdapter = apiClient.defaults.adapter;

function response(config: InternalAxiosRequestConfig, data: unknown, status = 200): AdapterResponse {
  return {
    data,
    status,
    statusText: status === 200 ? "OK" : "Error",
    headers: {},
    config,
  };
}

function failedResponse(config: InternalAxiosRequestConfig, status: number) {
  return {
    config,
    response: response(config, {message: "Request failed."}, status),
  };
}

describe("apiClient", () => {
  afterEach(() => {
    apiClient.defaults.adapter = originalAdapter;
  });

  it("returns parsed JSON from a successful request", async () => {
    apiClient.defaults.adapter = jest.fn((config: InternalAxiosRequestConfig) =>
      Promise.resolve(response(config, {id: 1, label: "Timing"})),
    ) as AxiosAdapter;

    const result = await apiClient.get<{id: number; label: string}>("/topics/1/");

    expect(result.data).toEqual({id: 1, label: "Timing"});
  });

  it("retries a GET request once after a 503 response", async () => {
    const adapter = jest
      .fn()
      .mockImplementationOnce((config: InternalAxiosRequestConfig) => Promise.reject(failedResponse(config, 503)))
      .mockImplementationOnce((config: InternalAxiosRequestConfig) =>
        Promise.resolve(response(config, {available: true})),
      );
    apiClient.defaults.adapter = adapter as AxiosAdapter;

    const result = await apiClient.get<{available: boolean}>("/status/");

    expect(result.data).toEqual({available: true});
    expect(adapter).toHaveBeenCalledTimes(2);
  });

  it("does not retry a non-retryable response", async () => {
    const adapter = jest.fn((config: InternalAxiosRequestConfig) =>
      Promise.reject(failedResponse(config, 400)),
    );
    apiClient.defaults.adapter = adapter as AxiosAdapter;

    await expect(apiClient.get("/invalid-request/")).rejects.toMatchObject({
      name: "ApiError",
      status: 400,
    });
    expect(adapter).toHaveBeenCalledTimes(1);
  });

  it("does not retry POST requests after a 503 response", async () => {
    const adapter = jest.fn((config: InternalAxiosRequestConfig) =>
      Promise.reject(failedResponse(config, 503)),
    );
    apiClient.defaults.adapter = adapter as AxiosAdapter;

    await expect(apiClient.post("/answers/", {selected_answer: "A"})).rejects.toMatchObject({
      name: "ApiError",
      status: 503,
    });
    expect(adapter).toHaveBeenCalledTimes(1);
  });
});

describe("unwrapList", () => {
  it("returns an array payload unchanged", () => {
    expect(unwrapList<number>([1, 2])).toEqual([1, 2]);
  });

  it("returns a results payload and handles missing results", () => {
    expect(unwrapList<number>({results: [1, 2]})).toEqual([1, 2]);
    expect(unwrapList<number>({})).toEqual([]);
  });
});
