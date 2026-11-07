import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Crypto from "expo-crypto";
import { Platform } from "react-native";
import * as Device from "expo-device";

let identity: Promise<string> | null = null;
const KEY = "pharmenta.device-id";

export function getDeviceId(): Promise<string> {
  if (!identity) identity = (async () => {
    try {
      const stored = await AsyncStorage.getItem(KEY);
      if (stored) return stored;
      const value = Crypto.randomUUID();
      await AsyncStorage.setItem(KEY, value);
      return value;
    } catch {
      return Crypto.randomUUID();
    }
  })();
  return identity;
}

export async function deviceHeaders(): Promise<Record<string, string>> {
  return {
    "X-Device-ID": await getDeviceId(),
    "X-Client-Platform": Platform.OS === "web" ? "web" : Platform.OS,
    ...(Platform.OS !== "web" ? { "X-Device-OS-Version": Device.osVersion ?? String(Platform.Version) } : {}),
    ...(Platform.OS !== "web" && Device.modelName ? { "X-Device-Model": Device.modelName } : {}),
  };
}
