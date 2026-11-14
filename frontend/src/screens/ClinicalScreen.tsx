import React from "react";
import { Pressable, View } from "react-native";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { IconImage, IconName } from "@/components/primitives/IconImage";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { StringKey } from "@/i18n/strings";
import { ScreenKey } from "@/navigation/types";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";

const PATHS: { screen: ScreenKey; icon: IconName; label: StringKey; fa: string; en: string }[] = [
  { screen: "calculator", icon: "entry-calculator", label: "calculatorLabel", fa: "ابزارهای محاسبه و تنظیم دوز", en: "Clinical tools and dose adjustment" },
  { screen: "guidelines", icon: "entry-guidelines", label: "guidelinesLabel", fa: "راهنماهای بالینی و درمانی", en: "Clinical and treatment guidelines" },
  { screen: "diseasesConditions", icon: "entry-diseases", label: "diseasesConditionsLabel", fa: "مرور بیماری‌ها و شرایط بالینی", en: "Diseases and clinical conditions" },
];

export function ClinicalScreen() {
  const { t, isFa, row } = useLang();
  const { colors } = useTheme();
  const navigate = useNav(s => s.navigate);
  const goBack = useNav(s => s.goBack);
  return <Screen>
    <ScreenChrome title={t("clinicalLabel")} onBack={goBack} />
    <AppText muted size={13} style={{ marginBottom: 20 }}>{isFa ? "ابزارها و منابع موردنیاز در کار بالینی" : "Tools and references for clinical practice"}</AppText>
    <View testID="clinical-paths" style={{ gap: 12 }}>{PATHS.map(path => <Pressable key={path.screen} accessibilityRole="button" onPress={() => navigate(path.screen)}>
      <Card style={{ flexDirection: row, alignItems: "center", gap: 14 }}>
        <IconImage name={path.icon} size={44} />
        <View style={{ flex: 1, gap: 5 }}><AppText weight="800" size={15}>{t(path.label)}</AppText><AppText muted size={12}>{isFa ? path.fa : path.en}</AppText></View>
        <AppText size={24} color={colors.accent}>{isFa ? "‹" : "›"}</AppText>
      </Card>
    </Pressable>)}</View>
  </Screen>;
}
