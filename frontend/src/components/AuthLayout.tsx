import React from "react";
import { ScrollView, View } from "react-native";

import { AppShell } from "@/components/AppShell";
import { GlassToggles } from "@/components/GlassToggles";
import { HeaderMesh } from "@/components/HeaderMesh";
import { AppText } from "@/components/primitives/AppText";
import { IconImage } from "@/components/primitives/IconImage";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

/** The signed-out screens' frame: the brand on the teal header mesh, and a
 * sheet below it holding the form. */
export function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  const { t } = useLang();
  const { colors } = useTheme();
  return (
    <AppShell>
      <HeaderMesh bleedTop>
        {/* Keyboard avoidance is handled once, centrally, by AppShell. */}
        <View style={{ flex: 1 }}>
          <GlassToggles />

          <View style={{ flex: 1, alignItems: "center", justifyContent: "center", paddingHorizontal: 32 }}>
            <IconImage name="app-logo" size={96} style={{ marginBottom: 16 }} />
            <AppText weight="900" size={26} color="#fff" center>
              {t("appName")}
            </AppText>
            {/* The header mesh is a dark teal gradient in BOTH themes, so this
                text must stay light — `onAccentSub` flips to near-black in dark
                mode (it is tuned for text on the light accent pill). */}
            <AppText weight="600" size={14} color="rgba(255,255,255,0.85)" center style={{ marginTop: 8 }}>
              {t("tagline")}
            </AppText>
          </View>

          <View
            style={{
              backgroundColor: colors.appBg,
              borderTopLeftRadius: 28,
              borderTopRightRadius: 28,
              paddingHorizontal: 26,
              paddingTop: 28,
              paddingBottom: 34,
            }}
          >
            <ScrollView keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
              <AppText weight="800" size={20}>
                {title}
              </AppText>
              <AppText muted weight="600" size={13} style={{ marginTop: 4, marginBottom: 20, lineHeight: 21 }}>
                {subtitle}
              </AppText>
              {children}
            </ScrollView>
          </View>
        </View>
      </HeaderMesh>
    </AppShell>
  );
}
