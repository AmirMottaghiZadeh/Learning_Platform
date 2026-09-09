import React from "react";
import { Modal, Pressable, View } from "react-native";

import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

export type HelpKey =
  | "dashboard"
  | "quiz"
  | "flashcards"
  | "lessons"
  | "mistakes"
  | "statistics"
  | "planning";

// Condensed from the design's HELP_CONTENT.
const HELP: Record<HelpKey, { fa: [string, string[]]; en: [string, string[]] }> = {
  dashboard: {
    fa: ["راهنمای داشبورد", ["بالای صفحه، خوش‌آمدگویی و وضعیت روزانه‌ت را می‌بینی.", "با میان‌برها مستقیم به هر بخش می‌روی.", "کارت پایین، فصل بعدی پیشنهادی برای مطالعه است."]],
    en: ["Dashboard guide", ["The top shows your greeting and today's status.", "The shortcuts jump straight to each section.", "The bottom card is your suggested next chapter."]],
  },
  quiz: {
    fa: ["راهنمای آزمون", ["هر سؤال یک‌بار قابل پاسخ است؛ بعدش جواب درست نشان داده می‌شود.", "در پایان، امتیاز کلی و گزینهٔ تلاش دوباره را می‌بینی.", "سؤال‌ها بر اساس داروهای پرتکرار ساخته شده‌اند."]],
    en: ["Quiz guide", ["Each question is answered once; the answer is revealed after.", "At the end you see your score and a retry option.", "Questions are built around frequently-used drugs."]],
  },
  flashcards: {
    fa: ["راهنمای فلش‌کارت", ["روی کارت بزن تا برگردد و جواب را ببینی.", "بعد از دیدن جواب، آسان یا سخت بودنش را مشخص کن.", "با «جعبهٔ لایتنر» به مرور زمان‌بندی‌شده دسترسی داری."]],
    en: ["Flashcards guide", ["Tap the card to flip it and see the answer.", "After the answer, rate it easy or hard.", "Use the Leitner box for scheduled review."]],
  },
  lessons: {
    fa: ["راهنمای درسنامه", ["دروس بر اساس کد ATC به گروه و زیرگروه تقسیم شده‌اند.", "روی هر گروه بزن تا زیرگروه‌هایش باز شود.", "نوار رنگی هر زیرگروه، درصد مطالعهٔ همان بخش را نشان می‌دهد."]],
    en: ["Lessons guide", ["Lessons are grouped by ATC code into groups and subgroups.", "Tap a group to expand its subgroups.", "Each bar shows study progress for that section."]],
  },
  mistakes: {
    fa: ["راهنمای اشتباهات", ["هر مورد، موضوعی است که بیشترین اشتباه را در آن داشتی.", "روی هر مورد بزن تا جزئیات و توصیهٔ مرور را ببینی.", "تمرکز روی این‌ها سریع‌ترین راه جبران ضعف است."]],
    en: ["Mistakes guide", ["Each item is a topic where you made the most mistakes.", "Tap an item for details and a review tip.", "Focusing here is the fastest way to close gaps."]],
  },
  statistics: {
    fa: ["راهنمای آمار", ["نمودار هفتگی، میزان مطالعهٔ روزانه‌ات را نشان می‌دهد.", "دایرهٔ پیشرفت، درصد تسلط کلی است.", "این آمار بعد از هر آزمون و مرور به‌روز می‌شود."]],
    en: ["Statistics guide", ["The weekly chart shows your daily study time.", "The ring shows overall mastery.", "Stats update after each quiz and review."]],
  },
  planning: {
    fa: ["راهنمای برنامه‌ریزی", ["روزهایی که می‌خواهی مطالعه کنی را انتخاب کن.", "برنامه را ذخیره کن تا یادآوری روزانه فعال شود.", "هر زمان می‌توانی برنامه را دوباره ویرایش کنی."]],
    en: ["Planning guide", ["Pick the days you want to study.", "Save the plan to enable daily reminders.", "You can edit the plan again anytime."]],
  },
};

export function HelpSheet({
  helpKey,
  onClose,
}: {
  helpKey: HelpKey | null;
  onClose: () => void;
}) {
  const { colors } = useTheme();
  const { lang } = useLang();
  if (!helpKey) return null;
  const [title, items] = HELP[helpKey][lang];

  return (
    <Modal transparent animationType="slide" visible onRequestClose={onClose}>
      <Pressable
        onPress={onClose}
        style={{ flex: 1, backgroundColor: "rgba(4,10,9,0.35)", justifyContent: "flex-end" }}
      >
        <Pressable
          style={{
            backgroundColor: colors.cardBg,
            borderTopLeftRadius: 24,
            borderTopRightRadius: 24,
            padding: 22,
            paddingBottom: 34,
          }}
        >
          <View
            style={{
              width: 40,
              height: 4,
              borderRadius: 2,
              backgroundColor: colors.trackBg,
              alignSelf: "center",
              marginBottom: 16,
            }}
          />
          <AppText weight="800" size={17} style={{ marginBottom: 14 }}>
            {title}
          </AppText>
          <View style={{ gap: 12 }}>
            {items.map((it, i) => (
              <View key={i} style={{ flexDirection: "row", gap: 10 }}>
                <View
                  style={{
                    width: 22,
                    height: 22,
                    borderRadius: 11,
                    backgroundColor: colors.accent + "1a",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <AppText weight="900" size={11} color={colors.accent}>
                    {i + 1}
                  </AppText>
                </View>
                <AppText weight="600" size={13} muted style={{ flex: 1, lineHeight: 21 }}>
                  {it}
                </AppText>
              </View>
            ))}
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}
