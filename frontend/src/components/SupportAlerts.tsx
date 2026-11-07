import React, { useEffect, useRef, useState } from "react";
import { Pressable, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useSupportSummary } from "@/notifications/useSupportNotifications";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { layout } from "@/theme/tokens";

export function SupportAlerts() {
  const { isFa, row, n } = useLang(), { colors, shadows } = useTheme();
  const insets = useSafeAreaInsets();
  const userId = useAuth(s => s.user?.id), screen = useNav(s => s.screen), navigate = useNav(s => s.navigate);
  const { data } = useSupportSummary();
  const [visible, setVisible] = useState(false);
  const previous = useRef(0);
  useEffect(() => { previous.current = 0; setVisible(false); }, [userId]);
  useEffect(() => {
    const unread = data?.unread ?? 0;
    if (unread > previous.current && screen !== "support") setVisible(true);
    if (!unread || screen === "support") setVisible(false);
    previous.current = unread;
  }, [data?.unread, screen]);
  useEffect(() => {
    if (!visible) return;
    const timer = setTimeout(() => setVisible(false), 6000);
    return () => clearTimeout(timer);
  }, [visible, data?.unread]);
  if (!visible || !userId) return null;
  return <View style={[{ position: "absolute", top: insets.top + 8, alignSelf: "center", width: "94%", maxWidth: layout.appMaxWidth - 24, flexDirection: row, alignItems: "center", gap: 12, borderRadius: 16, backgroundColor: colors.cardBg, paddingHorizontal: 14, borderWidth: 1, borderColor: colors.trackBg }, shadows.raisedSm]} accessibilityLiveRegion="polite"><Pressable onPress={() => { setVisible(false); navigate("support"); }} accessibilityRole="button" style={{ flex: 1, minHeight: 70, justifyContent: "center", gap: 3 }}><AppText weight="800" color={colors.accent}>{isFa ? "پیام تازه از پشتیبانی" : "New support reply"}</AppText><AppText size={12} muted>{isFa ? `${n(data?.unread ?? 0)} پیام خوانده‌نشده · مشاهدهٔ گفت‌وگو` : `${data?.unread ?? 0} unread · Open conversation`}</AppText></Pressable><Pressable onPress={() => setVisible(false)} accessibilityRole="button" accessibilityLabel={isFa ? "بستن اعلان" : "Dismiss notification"} style={{ width: 44, height: 44, alignItems: "center", justifyContent: "center" }}><AppText muted size={18}>×</AppText></Pressable></View>;
}
