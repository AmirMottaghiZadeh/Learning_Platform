import React from "react";
import { Pressable, View } from "react-native";

import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { BG_TONES, DEFAULT_TONE, THEME, ThemeMode } from "@/theme/tokens";
import { SupportLink, NotificationSettings } from "@/components/SupportSettings";

const MODES: ThemeMode[] = ["light", "dark"];

/** The app's settings: the theme, and for each theme its background tone --
 * four, from the lightest to the deepest. Picking a tone of the other theme
 * switches to that theme, so the choice is seen at once. */
export function SettingsScreen() {
  const { t, n, row } = useLang();
  const { colors, mode, tones, setMode, setTone } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);

  return (
    <Screen>
      <ScreenChrome title={t("settingsTitle")} onBack={goBack} />

      <View style={{ gap: 12, marginBottom: 24 }}>
        <SupportLink />
        <Pressable onPress={() => navigate("plans")} accessibilityRole="button"><Card><AppText weight="800">{t("profileBuySubscription")}</AppText></Card></Pressable>
        <Pressable onPress={() => navigate("devices")} accessibilityRole="button"><Card><AppText weight="800">{t("devicesTitle")}</AppText></Card></Pressable>
        <NotificationSettings />
      </View>

      <AppText weight="800" size={13} muted style={{ marginBottom: 8 }}>
        {t("settingsAppearance")}
      </AppText>

      <Card raised style={{ gap: 18 }}>
        <View style={{ gap: 10 }}>
          <AppText weight="800" size={14}>
            {t("settingsTheme")}
          </AppText>
          <View style={{ flexDirection: row, gap: 10 }}>
            {MODES.map((m) => {
              const on = mode === m;
              return (
                <Pressable
                  key={m}
                  onPress={() => setMode(m)}
                  accessibilityRole="radio"
                  accessibilityState={{ selected: on }}
                  style={{
                    flex: 1,
                    height: 46,
                    borderRadius: 14,
                    flexDirection: row,
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 8,
                    backgroundColor: on ? colors.accent : colors.softBg,
                    borderWidth: 1,
                    borderColor: on ? colors.accent : colors.trackBg,
                  }}
                >
                  <AppText size={14} color={on ? colors.onAccent : colors.ink}>
                    {m === "light" ? "☀" : "☾"}
                  </AppText>
                  <AppText weight="800" size={13.5} color={on ? colors.onAccent : colors.ink}>
                    {t(m === "light" ? "settingsLight" : "settingsDark")}
                  </AppText>
                </Pressable>
              );
            })}
          </View>
        </View>

        {MODES.map((m) => (
          <View key={m} style={{ gap: 10 }}>
            <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
              <AppText weight="800" size={14}>
                {t(m === "light" ? "settingsBgLight" : "settingsBgDark")}
              </AppText>
              {mode === m ? (
                <AppText weight="700" size={11.5} color={colors.accent}>
                  {t("settingsInUse")}
                </AppText>
              ) : null}
            </View>
            {/* lightest to deepest, in reading order */}
            <View style={{ flexDirection: row, gap: 10 }}>
              {BG_TONES[m].map((tone, i) => {
                const on = tones[m] === i;
                const card = tone.cardBg ?? THEME[m].cardBg;
                return (
                  <Pressable
                    key={i}
                    onPress={() => {
                      setTone(m, i);
                      if (mode !== m) setMode(m);
                    }}
                    accessibilityRole="radio"
                    accessibilityState={{ selected: on }}
                    accessibilityLabel={`${t(m === "light" ? "settingsBgLight" : "settingsBgDark")} ${i + 1}`}
                    style={{ flex: 1, alignItems: "center", gap: 6 }}
                  >
                    <View
                      style={{
                        width: "100%",
                        aspectRatio: 0.8,
                        borderRadius: 14,
                        padding: 7,
                        gap: 5,
                        backgroundColor: tone.appBg,
                        borderWidth: on ? 3 : 1,
                        borderColor: on ? colors.accent : colors.trackBg,
                        justifyContent: "flex-end",
                      }}
                    >
                      {/* a card on the background, as screens show them */}
                      <View style={{ height: 12, borderRadius: 4, backgroundColor: card }} />
                      <View style={{ height: 12, width: "70%", borderRadius: 4, backgroundColor: card }} />
                    </View>
                    <AppText weight={on ? "800" : "600"} size={11.5} color={on ? colors.accent : colors.muted}>
                      {i === DEFAULT_TONE ? t("settingsDefault") : n(i + 1)}
                    </AppText>
                  </Pressable>
                );
              })}
            </View>
          </View>
        ))}
      </Card>
    </Screen>
  );
}
