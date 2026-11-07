import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { useEffect, useState } from "react";
import { Pressable, Switch, View } from "react-native";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { useLang } from "@/i18n/LanguageProvider";
import { useSupportSummary } from "@/notifications/useSupportNotifications";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";

export function SupportLink() {
  const { isFa, row, n } = useLang();
  const { colors } = useTheme();
  const navigate = useNav(s => s.navigate);
  const { data } = useSupportSummary();
  return <Pressable onPress={() => navigate("support")} accessibilityRole="button"><Card style={{ flexDirection: row, alignItems: "center", gap: 12, minHeight: 68 }}><View style={{ flex: 1, gap: 3 }}><AppText weight="800" size={14}>{isFa ? "پشتیبانی" : "Support"}</AppText><AppText muted size={12}>{isFa ? "گفت‌وگو با تیم فارمنتا" : "Chat with the Pharmenta team"}</AppText></View>{data?.unread ? <AppText weight="800" color={colors.accent}>{n(data.unread)}</AppText> : null}<AppText muted>{isFa ? "‹" : "›"}</AppText></Card></Pressable>;
}

export function NotificationSettings() {
  const { data } = useSupportSummary();
  return data?.push_enabled === true ? <ActiveNotificationSettings /> : null;
}

function ActiveNotificationSettings() {
  const { isFa, row } = useLang();
  const { colors } = useTheme();
  const userId = useAuth(s => s.user?.id);
  const [runtime, setRuntime] = useState<typeof import("@/notifications/registration") | null>(null);
  const [enabled, setEnabled] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const supported = runtime?.notificationSupport() ?? false;
  useEffect(() => {
    let alive = true;
    setEnabled(false);
    void import("@/notifications/registration").then(async registration => {
      const [value, permission] = await Promise.all([AsyncStorage.getItem(`pharmenta.notifications.${userId}`), registration.notificationPermission()]);
      if (alive) { setRuntime(registration); setEnabled(value === "on" && permission); }
    }).catch(() => undefined);
    return () => { alive = false; };
  }, [userId]);
  const change = async (value: boolean) => {
    if (!runtime) return;
    setBusy(true); setError("");
    try {
      if (value) await runtime.enableSupportNotifications(); else await runtime.disableSupportNotifications();
      if (useAuth.getState().user?.id !== userId) return;
      await AsyncStorage.setItem(`pharmenta.notifications.${userId}`, value ? "on" : "off"); setEnabled(value);
    } catch (e) { setError(e instanceof Error ? e.message : isFa ? "تنظیم اعلان انجام نشد." : "Could not update notifications."); }
    finally { setBusy(false); }
  };
  return <Card style={{ gap: 10 }}><View style={{ flexDirection: row, alignItems: "center", gap: 12 }}><View style={{ flex: 1, gap: 4 }}><AppText weight="800" size={14}>{isFa ? "اعلان پیام‌های پشتیبانی" : "Support message notifications"}</AppText><AppText muted size={12}>{supported ? (isFa ? "با رسیدن پاسخ تازه مطلع شوید." : "Get notified when our team replies.") : (isFa ? "اعلان سیستم در این محیط پشتیبانی نمی‌شود؛ پیام‌ها در بخش پشتیبانی در دسترس‌اند." : "System notifications are unavailable here. Messages remain in Support.")}</AppText></View><Switch accessibilityLabel={isFa ? "فعال‌سازی اعلان پشتیبانی" : "Enable support notifications"} value={enabled} onValueChange={v => void change(v)} disabled={busy || !supported} trackColor={{ false: colors.trackBg, true: colors.accent }} thumbColor={colors.cardBg} /></View>{busy ? <AppText muted size={12}>{isFa ? "در حال تنظیم…" : "Updating…"}</AppText> : null}{error ? <AppText size={12} color={colors.denyLabel}>{error}</AppText> : null}</Card>;
}
