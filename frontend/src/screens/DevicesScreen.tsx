import { useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { Alert, Platform, Pressable, View } from "react-native";
import { apiClient } from "@/api/client";
import { Screen } from "@/components/primitives/Screen";
import { Card } from "@/components/primitives/Card";
import { AppText } from "@/components/primitives/AppText";
import { ScreenChrome } from "@/components/ScreenChrome";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useAuth } from "@/store/auth";
import { useTheme } from "@/theme/ThemeProvider";

type DeviceSession = { id: string; device_name: string; os_name: string; os_version: string; browser: string; ip_address: string; current: boolean; is_active?: boolean; last_used_at: string; revoked_at: string | null; refresh_expires_at: string };

export function DevicesScreen() {
  const { isFa } = useLang(), { colors } = useTheme();
  const goBack = useNav(s => s.goBack), userId = useAuth(s => s.user?.id);
  const [error, setError] = useState("");
  const query = useQuery({ queryKey: ["my-devices", userId], queryFn: () => apiClient.get<DeviceSession[]>("/auth/sessions/").then(r => r.data), staleTime: 0 });
  const revoke = async (device: DeviceSession) => {
    try { await apiClient.post(`/auth/sessions/${device.id}/revoke/`, { reason: "user_device_removed" }); await query.refetch(); }
    catch { setError(isFa ? "پایان دسترسی انجام نشد؛ دوباره تلاش کنید." : "Could not sign out this device. Try again."); }
  };
  const confirm = (device: DeviceSession) => {
    const message = isFa ? "دسترسی این دستگاه به حساب پایان یابد؟" : "Sign this device out of your account?";
    if (Platform.OS === "web") { if (window.confirm(message)) void revoke(device); }
    else Alert.alert(isFa ? "پایان دسترسی دستگاه" : "Sign out device", message, [{ text: isFa ? "انصراف" : "Cancel", style: "cancel" }, { text: isFa ? "پایان دسترسی" : "Sign out", style: "destructive", onPress: () => void revoke(device) }]);
  };
  const devices = query.data?.filter(s => s.is_active !== false && !s.revoked_at && new Date(s.refresh_expires_at).getTime() > Date.now()) ?? [];
  return <Screen><ScreenChrome title={isFa ? "دستگاه‌های من" : "My devices"} onBack={goBack} /><AppText muted size={13} style={{ marginBottom: 16 }}>{isFa ? "حساب شما هم‌زمان روی حداکثر دو دستگاه قابل استفاده است." : "Your account supports up to two signed-in devices."}</AppText>{query.isPending ? <AppText muted>…</AppText> : query.isError ? <Pressable onPress={() => void query.refetch()}><AppText color={colors.denyLabel}>{isFa ? "دریافت دستگاه‌ها انجام نشد؛ تلاش دوباره" : "Could not load devices. Retry"}</AppText></Pressable> : <View style={{ gap: 12 }}>{devices.map(device => <Card key={device.id} style={{ gap: 8 }}><AppText weight="800">{device.os_name || device.device_name || (isFa ? "دستگاه نامشخص" : "Unknown device")} {device.os_version}</AppText><AppText muted size={12}>{device.browser}{device.current ? (isFa ? " · همین دستگاه" : " · This device") : ""}</AppText><AppText size={12} style={{ writingDirection: "ltr", textAlign: "left" }}>IP: {device.ip_address || "—"}</AppText><AppText muted size={12}>{new Date(device.last_used_at).toLocaleString(isFa ? "fa-IR" : "en")}</AppText>{!device.current ? <Pressable onPress={() => confirm(device)} accessibilityRole="button" style={{ minHeight: 44, justifyContent: "center" }}><AppText weight="700" color={colors.denyLabel}>{isFa ? "پایان دسترسی این دستگاه" : "Sign out this device"}</AppText></Pressable> : null}</Card>)}</View>}{error ? <AppText color={colors.denyLabel}>{error}</AppText> : null}</Screen>;
}
