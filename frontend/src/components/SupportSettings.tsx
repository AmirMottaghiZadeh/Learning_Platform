import React from "react";
import { Pressable, View } from "react-native";
import { AppText } from "@/components/primitives/AppText";
import { Chevron } from "@/components/primitives/Chevron";
import { Card } from "@/components/primitives/Card";
import { useLang } from "@/i18n/LanguageProvider";
import { useSupportSummary } from "@/notifications/useSupportNotifications";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";

export function SupportLink() {
  const { isFa, row, n } = useLang();
  const { colors } = useTheme();
  const navigate = useNav(s => s.navigate);
  const { data } = useSupportSummary();
  return <Pressable onPress={() => navigate("support")} accessibilityRole="button"><Card style={{ flexDirection: row, alignItems: "center", gap: 12, minHeight: 68 }}><View style={{ flex: 1, gap: 3 }}><AppText weight="800" size={14}>{isFa ? "پشتیبانی" : "Support"}</AppText><AppText muted size={12}>{isFa ? "گفت‌وگو با تیم فارمنتا" : "Chat with the Pharmenta team"}</AppText></View>{data?.unread ? <AppText weight="800" color={colors.accent}>{n(data.unread)}</AppText> : null}<Chevron /></Card></Pressable>;
}
