import AsyncStorage from "@react-native-async-storage/async-storage";
import {act, renderHook, waitFor} from "@testing-library/react-native";
import React from "react";

import {platformApi} from "../api/platform";
import type {User} from "../types/api";
import {AuthProvider, useAuth} from "./auth";

jest.mock("../api/platform", () => ({
  platformApi: {
    login: jest.fn(),
    logout: jest.fn(),
    me: jest.fn(),
    register: jest.fn(),
  },
}));

const user: User = {
  id: 1,
  first_name: "Ali",
  last_name: "Ahmadi",
  username: "learner",
  email: "learner@example.com",
};
const storage = AsyncStorage as jest.Mocked<typeof AsyncStorage>;
const api = platformApi as jest.Mocked<typeof platformApi>;

function wrapper({children}: {children: React.ReactNode}) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe("AuthProvider", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    storage.getItem.mockResolvedValue(null);
  });

  it("stores the token and user after a successful login", async () => {
    api.login.mockResolvedValue({token: "token-123", user});
    const {result} = renderHook(() => useAuth(), {wrapper});

    await waitFor(() => expect(result.current.loading).toBe(false));
    await act(async () => {
      await result.current.signIn("learner", "secret");
    });

    expect(api.login).toHaveBeenCalledWith("learner", "secret");
    expect(storage.setItem).toHaveBeenCalledWith("pharmexa_auth_token", "token-123");
    expect(result.current.token).toBe("token-123");
    expect(result.current.user).toEqual(user);
  });

  it("clears local auth state even when remote logout succeeds", async () => {
    api.login.mockResolvedValue({token: "token-123", user});
    api.logout.mockResolvedValue(null);
    const {result} = renderHook(() => useAuth(), {wrapper});

    await waitFor(() => expect(result.current.loading).toBe(false));
    await act(async () => {
      await result.current.signIn("learner", "secret");
    });
    await waitFor(() => expect(result.current.token).toBe("token-123"));
    await act(async () => {
      await result.current.signOut();
    });

    expect(storage.removeItem).toHaveBeenCalledWith("pharmexa_auth_token");
    expect(api.logout).toHaveBeenCalledWith("token-123");
    expect(result.current.token).toBeNull();
    expect(result.current.user).toBeNull();
  });

  it("restores a persisted session when its token can load a profile", async () => {
    storage.getItem.mockResolvedValue("stored-token");
    api.me.mockResolvedValue(user);

    const {result} = renderHook(() => useAuth(), {wrapper});

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(api.me).toHaveBeenCalledWith("stored-token");
    expect(result.current.token).toBe("stored-token");
    expect(result.current.user).toEqual(user);
  });

  it("clears an unusable persisted session without blocking startup", async () => {
    storage.getItem.mockResolvedValue("corrupted-token");
    api.me.mockRejectedValue(new Error("Invalid token"));

    const {result} = renderHook(() => useAuth(), {wrapper});

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(storage.removeItem).toHaveBeenCalledWith("pharmexa_auth_token");
    expect(result.current.token).toBeNull();
    expect(result.current.user).toBeNull();
  });
});
