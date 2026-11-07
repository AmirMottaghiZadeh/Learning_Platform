import React from "react";
import { Screen } from "@/components/primitives/Screen";
import { ScreenChrome } from "@/components/ScreenChrome";
import { NotificationSettings } from "@/components/SupportSettings";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";

export function NotificationsScreen() {
  const { isFa } = useLang(), goBack = useNav(s => s.goBack);
  return <Screen><ScreenChrome title={isFa ? "اعلان‌ها" : "Notifications"} onBack={goBack} /><NotificationSettings /></Screen>;
}
