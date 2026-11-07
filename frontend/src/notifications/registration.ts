import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import Constants from "expo-constants";
import { Platform } from "react-native";
import { AppState } from "react-native";
import { getDeviceId } from "@/api/device";
import { supportApi } from "@/api/support";
import { useNav } from "@/store/nav";
import { useAuth } from "@/store/auth";

export function notificationSupport(): boolean { return Platform.OS === "android"; }

async function register(ask: boolean): Promise<void> {
  const owner = useAuth.getState().user?.id;
  if (Platform.OS !== "android" || !Device.isDevice) throw new Error("برای اعلان اندروید، اپ را روی گوشی واقعی اجرا کنید.");
  await Notifications.setNotificationChannelAsync("support", { name: "پشتیبانی فارمنتا", importance: Notifications.AndroidImportance.HIGH });
  let permission = await Notifications.getPermissionsAsync();
  if (!permission.granted && ask) permission = await Notifications.requestPermissionsAsync();
  if (!permission.granted) throw new Error("اجازهٔ اعلان داده نشده است؛ آن را در تنظیمات گوشی فعال کنید.");
  const projectId = Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;
  if (!projectId) throw new Error("شناسهٔ پروژهٔ اعلان در این نسخه تنظیم نشده است.");
  let token: string;
  try { token = (await Notifications.getExpoPushTokenAsync({ projectId })).data; }
  catch { throw new Error("دریافت توکن اعلان انجام نشد. اتصال و تنظیم Firebase/FCM این بیلد باید بررسی شود."); }
  if (!owner || useAuth.getState().user?.id !== owner) return;
  await supportApi.subscribe({ device_id: await getDeviceId(), platform: "android", enabled: true, expo_token: token });
}

export const enableSupportNotifications = () => register(true);
export async function notificationPermission(): Promise<boolean> {
  return Platform.OS === "android" && (await Notifications.getPermissionsAsync()).granted;
}
export async function refreshSupportNotifications(): Promise<void> {
  if (await notificationPermission()) await register(false);
}

export async function disableSupportNotifications(): Promise<void> {
  if (Platform.OS === "android") await supportApi.subscribe({ device_id: await getDeviceId(), platform: "android", enabled: false });
}

export function listenSupportNotifications(onOpen: (conversationId: string) => void): () => void {
  if (Platform.OS !== "android") return () => undefined;
  Notifications.setNotificationHandler({ handleNotification: async () => {
    const readingChat = AppState.currentState === "active" && useNav.getState().screen === "support";
    return { shouldShowBanner: !readingChat, shouldShowList: !readingChat, shouldPlaySound: !readingChat, shouldSetBadge: true };
  } });
  const open = (response: Notifications.NotificationResponse | null) => {
    const id = response?.notification.request.content.data?.conversationId;
    if (typeof id === "string" && /^[a-f0-9-]{36}$/i.test(id)) {
      onOpen(id);
      void Notifications.clearLastNotificationResponseAsync().catch(() => undefined);
    }
  };
  const subscription = Notifications.addNotificationResponseReceivedListener(open);
  void Notifications.getLastNotificationResponseAsync().then(open).catch(() => undefined);
  return () => subscription.remove();
}
