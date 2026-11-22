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
export function AuthLayout({ title, subtitle, children, panel = false, compact = false }: { title: string; subtitle: string; children: React.ReactNode; panel?: boolean; compact?: boolean }) {
  const { t } = useLang();
  const { colors } = useTheme();
  return (
    <AppShell>
      <HeaderMesh bleedTop>
        {/* Keyboard avoidance is handled once, centrally, by AppShell. */}
        <View style={{ flex: 1 }}>
          <GlassToggles />

          <View style={compact
            ? { flexDirection: "row", justifyContent: "center", alignItems: "center", paddingTop: 8, paddingBottom: 16, gap: 8 }
            : { flex: 1, alignItems: "center", justifyContent: "center", paddingHorizontal: 24, paddingVertical: 8 }}>
            <IconImage name="app-logo" size={compact ? 36 : 64} style={{ marginBottom: compact ? 0 : 8 }} />
            <AppText weight="700" size={compact ? 17 : 23} color="#fff" center>{t("appName")}</AppText>
            {!compact ? <AppText size={13} color="rgba(255,255,255,0.85)" center style={{ marginTop: 4 }}>{t("tagline")}</AppText> : null}
          </View>

          <View
            style={{
              backgroundColor: colors.appBg,
              width: "100%",
              maxWidth: 580,
              alignSelf: "center",
              borderTopLeftRadius: 28,
              borderTopRightRadius: 28,
              paddingHorizontal: 20,
              paddingTop: 24,
              paddingBottom: 24,
              maxHeight: compact ? undefined : "84%",
              flexGrow: compact ? 1 : undefined,
              flexShrink:1,
            }}
          >
            <ScrollView style={compact ? { flex: 1 } : undefined} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
              <AppText accessibilityRole="header" aria-level={1} weight="700" size={21}>
                {title}
              </AppText>
              <AppText muted weight="600" size={13} style={{ marginTop: 4, marginBottom: 20, lineHeight: 21 }}>
                {subtitle}
              </AppText>
              {panel ? <View style={{padding:16,borderRadius:16,backgroundColor:colors.cardBg}}>{children}</View> : children}
            </ScrollView>
          </View>
        </View>
      </HeaderMesh>
    </AppShell>
  );
}
