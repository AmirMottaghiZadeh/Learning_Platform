import { getDeviceId } from "@/api/device";
import { supportApi } from "@/api/support";
import { useAuth } from "@/store/auth";

export function notificationSupport(): boolean {
  return typeof window !== "undefined" && window.isSecureContext && "Notification" in window && "serviceWorker" in navigator && "PushManager" in window;
}

export async function enableSupportNotifications(): Promise<void> {
  const owner = useAuth.getState().user?.id;
  if (!notificationSupport()) throw new Error("این مرورگر از اعلان وب پشتیبانی نمی‌کند؛ نسخهٔ HTTPS وب‌اپ را باز کنید.");
  const config = await supportApi.summary();
  if (!config.push_enabled) throw new Error("اعلان‌های پشتیبانی فعلاً غیرفعال هستند.");
  if (!config.web_push_configured) throw new Error("کلید ارسال اعلان وب هنوز در سرور تنظیم نشده است.");
  const permission = await Notification.requestPermission();
  if (permission !== "granted") throw new Error("اجازهٔ اعلان داده نشد؛ از تنظیمات مرورگر آن را فعال کنید.");
  const registration = await navigator.serviceWorker.register("sw.js", { scope: "./" });
  await navigator.serviceWorker.ready;
  const raw = config.web_push_public_key.replace(/-/g, "+").replace(/_/g, "/");
  const decoded = atob(raw + "=".repeat((4 - raw.length % 4) % 4));
  const key = new Uint8Array(decoded.length);
  for (let i = 0; i < decoded.length; i++) key[i] = decoded.charCodeAt(i);
  const subscription = await registration.pushManager.getSubscription() ?? await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key });
  if (!owner || useAuth.getState().user?.id !== owner) return;
  await supportApi.subscribe({ device_id: await getDeviceId(), platform: "web", enabled: true, web_subscription: subscription.toJSON() });
}

export async function disableSupportNotifications(): Promise<void> {
  await supportApi.subscribe({ device_id: await getDeviceId(), platform: "web", enabled: false });
  const registration = await navigator.serviceWorker.getRegistration();
  const subscription = await registration?.pushManager.getSubscription();
  await subscription?.unsubscribe();
}

export async function notificationPermission(): Promise<boolean> {
  return notificationSupport() && Notification.permission === "granted";
}

export async function refreshSupportNotifications(): Promise<void> {
  if (!(await supportApi.summary()).push_enabled) return;
  if (!await notificationPermission()) return;
  const registration = await navigator.serviceWorker.getRegistration();
  const subscription = await registration?.pushManager.getSubscription();
  if (subscription) await supportApi.subscribe({ device_id: await getDeviceId(), platform: "web", enabled: true, web_subscription: subscription.toJSON() });
}

export function listenSupportNotifications(onOpen: (conversationId: string) => void): () => void {
  const handler = (event: MessageEvent) => {
    if (event.data?.type === "support-open" && typeof event.data.conversationId === "string" && /^[a-f0-9-]{36}$/i.test(event.data.conversationId)) onOpen(event.data.conversationId);
  };
  navigator.serviceWorker?.addEventListener("message", handler);
  const params = new URLSearchParams(location.search), id = params.get("supportThread");
  if (id && /^[a-f0-9-]{36}$/i.test(id)) {
    onOpen(id); params.delete("supportThread");
    history.replaceState(history.state, "", location.pathname + (params.size ? "?" + params : "") + location.hash);
  }
  return () => navigator.serviceWorker?.removeEventListener("message", handler);
}
