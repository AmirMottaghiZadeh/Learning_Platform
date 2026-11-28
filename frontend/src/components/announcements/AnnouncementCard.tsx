import React from "react";
import { Pressable, View } from "react-native";
import Svg, { Path } from "react-native-svg";

import { AnnouncementKind, AppAnnouncement } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import type { InstallOutcome } from "@/pwa/types";
import { usePwaInstall } from "@/pwa/usePwaInstall";

const ICONS: Record<AnnouncementKind, string[]> = {
  news: ["M4 10v4l11 5V5L4 10z", "M15 9a3 3 0 0 1 0 6"],
  update: ["M12 19V5", "M6 11l6-6 6 6"],
  warning: ["M12 3L2 20h20z", "M12 10v4", "M12 17v.5"],
  offer: ["M20 12v8H4v-8", "M2 7h20v5H2z", "M12 22V7"],
};

/** The chip colours of each kind, light and dark. */
function kindColors(kind: AnnouncementKind, isDark: boolean, accent: string) {
  switch (kind) {
    case "update":
      return isDark ? { bg: "#15294A", fg: "#9DC1F5" } : { bg: "#E4EDFA", fg: "#1D4F91" };
    case "warning":
      return isDark ? { bg: "#3A2C0E", fg: "#F0C46A" } : { bg: "#FBEFD6", fg: "#7A5200" };
    case "offer":
      return isDark ? { bg: "#2A2140", fg: "#C9B3F2" } : { bg: "#F1EBFA", fg: "#6B4C9A" };
    default:
      return { bg: accent + (isDark ? "26" : "1A"), fg: accent };
  }
}

type Props = {
  item: AppAnnouncement;
  index: number;
  total: number;
  onPress: () => void;
  onDismiss: () => void;
  onPage: (step: 1 | -1) => void;
  /** in the dimmed first showing: a «بعداً» that lifts the shade */
  onLater?: () => void;
  installHelp?: InstallOutcome | null;
  installing?: boolean;
};

/** One announcement as the home's card (design form 1): its kind, title,
 * text, button, and -- with several -- which one of how many. */
export function AnnouncementCard({ item, index, total, onPress, onDismiss, onPage, onLater, installHelp, installing }: Props) {
  const { colors, shadows, isDark } = useTheme();
  const { isFa, n, row } = useLang();
  const tone = kindColors(item.kind, isDark, colors.accent);
  const isInstall = item.button?.kind === "pwa";
  const install = usePwaInstall();
  const help = installHelp === "accepted"
    ? (isFa ? "درخواست نصب پذیرفته شد؛ تکمیل نصب را در مرورگر دنبال کنید." : "Installation accepted. Follow your browser to finish installing.")
    : install.manual === "ios"
      ? (isFa ? "در Safari، دکمهٔ اشتراک‌گذاری (Share) را بزنید، «افزودن به صفحهٔ اصلی» (Add to Home Screen) و سپس «افزودن» (Add) را انتخاب کنید." : "In Safari, tap Share, then Add to Home Screen, then Add.")
      : (isFa ? "از منوی مرورگر، «نصب برنامه» (Install app) یا «افزودن به صفحهٔ اصلی» (Add to Home screen) را انتخاب کنید. اگر این گزینه نیست، سایت را در Chrome باز کنید." : "In your browser menu, choose Install app or Add to Home screen. If neither is available, open this site in Chrome.");
  return (
    <View
      accessibilityRole="summary"
      accessibilityLabel={`${item.kind_label}: ${item.title}`}
      style={[{ backgroundColor: colors.cardBg, borderRadius: 20, padding: 16, gap: 8 }, shadows.raised]}
    >
      <View style={{ flexDirection: row, alignItems: "center", gap: 8 }}>
        <View style={{ flexDirection: row, alignItems: "center", gap: 6, backgroundColor: tone.bg, borderRadius: 999, paddingHorizontal: 11, paddingVertical: 3 }}>
          <Svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke={tone.fg} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round">
            {ICONS[item.kind].map((d) => (
              <Path key={d} d={d} />
            ))}
          </Svg>
          <AppText weight="800" size={12} color={tone.fg}>
            {item.kind_label}
          </AppText>
        </View>
        {item.is_test ? (
          <AppText weight="700" size={11.5} muted>
            {isFa ? "آزمایشی، فقط شما" : "Test, only you"}
          </AppText>
        ) : null}
        <View style={{ flex: 1 }} />
        {item.dismissible && !isInstall ? (
          <Pressable
            onPress={onDismiss}
            accessibilityRole="button"
            accessibilityLabel={isFa ? "بستن این اعلان" : "Close this announcement"}
            hitSlop={6}
            style={{ width: 44, height: 44, margin: -12, alignItems: "center", justifyContent: "center" }}
          >
            <AppText weight="700" size={20} muted>
              ×
            </AppText>
          </Pressable>
        ) : null}
      </View>

      <AppText weight="900" size={16} style={{ lineHeight: 25 }}>
        {item.title}
      </AppText>
      <AppText weight="600" size={13} muted style={{ lineHeight: 22 }}>
        {item.body}
      </AppText>
      {isInstall && installHelp ? (
        <AppText size={13} weight="600" style={{ lineHeight: 23 }} accessibilityLiveRegion="polite">
          {installHelp === "dismissed" ? (isFa ? "نصب انجام نشد. هر وقت خواستید می‌توانید دوباره اقدام کنید. " : "Installation was cancelled. You can try again later. ") : ""}
          {installHelp === "error" ? (isFa ? "پنجرهٔ نصب باز نشد. " : "The install prompt could not open. ") : ""}
          {help}
        </AppText>
      ) : null}

      {item.button || onLater || total > 1 ? (
        <View style={{ flexDirection: row, alignItems: "center", gap: 12, marginTop: 4, flexWrap: "wrap" }}>
          {item.button ? (
            <Pressable
              onPress={onPress}
              disabled={isInstall && installing}
              accessibilityState={{ disabled: isInstall && !!installing, busy: isInstall && !!installing }}
              accessibilityRole={item.button.kind === "url" ? "link" : "button"}
              style={({ pressed }) => ({
                minHeight: 44,
                paddingHorizontal: 18,
                borderRadius: 13,
                backgroundColor: colors.accent,
                flexDirection: row,
                alignItems: "center",
                gap: 6,
                opacity: pressed ? 0.85 : 1,
              })}
            >
              <AppText weight="800" size={13.5} color={colors.onAccent}>
                {isInstall ? (isFa ? "نصب" : "Install") : item.button.label}
              </AppText>
              <AppText weight="900" size={14} color={colors.onAccent}>
                {isFa ? "‹" : "›"}
              </AppText>
            </Pressable>
          ) : null}
          {isInstall ? (
            <Pressable onPress={onDismiss} accessibilityRole="button" style={{ minHeight: 44, justifyContent: "center", paddingHorizontal: 4 }}>
              <AppText weight="700" size={13} muted>{isFa ? "دیگر نشان نده" : "Don't show again"}</AppText>
            </Pressable>
          ) : onLater ? (
            <Pressable onPress={onLater} accessibilityRole="button" style={{ minHeight: 44, justifyContent: "center", paddingHorizontal: 4 }}>
              <AppText weight="700" size={13} muted>
                {isFa ? "بعداً" : "Later"}
              </AppText>
            </Pressable>
          ) : null}
          {total > 1 ? (
            <View style={{ flexDirection: row, alignItems: "center", gap: 2, marginStart: "auto" }}>
              <Pressable
                onPress={() => onPage(-1)}
                disabled={index === 0}
                accessibilityRole="button"
                accessibilityLabel={isFa ? "اعلان قبلی" : "Previous announcement"}
                style={{ width: 36, height: 44, alignItems: "center", justifyContent: "center", opacity: index === 0 ? 0.35 : 1 }}
              >
                <AppText weight="900" size={17} muted>
                  {isFa ? "›" : "‹"}
                </AppText>
              </Pressable>
              <AppText weight="700" size={12} muted accessibilityLiveRegion="polite">
                {isFa ? `${n(index + 1)} از ${n(total)}` : `${index + 1} of ${total}`}
              </AppText>
              <Pressable
                onPress={() => onPage(1)}
                disabled={index === total - 1}
                accessibilityRole="button"
                accessibilityLabel={isFa ? "اعلان بعدی" : "Next announcement"}
                style={{ width: 36, height: 44, alignItems: "center", justifyContent: "center", opacity: index === total - 1 ? 0.35 : 1 }}
              >
                <AppText weight="900" size={17} muted>
                  {isFa ? "‹" : "›"}
                </AppText>
              </Pressable>
            </View>
          ) : null}
        </View>
      ) : null}
    </View>
  );
}
