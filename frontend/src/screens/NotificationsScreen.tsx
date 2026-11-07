import React from "react";
import { Screen } from "@/components/primitives/Screen";
import { ScreenChrome } from "@/components/ScreenChrome";
import { NotificationSettings } from "@/components/SupportSettings";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { AppText } from "@/components/primitives/AppText";
import { useSupportSummary } from "@/notifications/useSupportNotifications";

export function NotificationsScreen() {
  const { isFa } = useLang(), goBack = useNav(s => s.goBack);
  const enabled = useSupportSummary().data?.push_enabled === true;
  return <Screen><ScreenChrome title={isFa ? "اعلان‌ها" : "Notifications"} onBack={goBack} />{enabled ? <NotificationSettings /> : <AppText muted>{isFa ? "اعلان‌ها فعلاً غیرفعال هستند." : "Notifications are temporarily disabled."}</AppText>}</Screen>;
}
