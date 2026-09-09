import React from "react";
import { Pressable, View } from "react-native";

import { ScreenHeader } from "@/components/ScreenHeader";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

export function ProfileScreen() {
  const { t, toggle: toggleLang, isFa } = useLang();
  const { colors, toggle: toggleTheme, isDark } = useTheme();
  const user = useAuth((s) => s.user);
  const signOut = useAuth((s) => s.signOut);
  const navigate = useNav((s) => s.navigate);

  const name = user?.profile.display_name || user?.first_name || user?.username || "";

  const Row = ({ label, onPress }: { label: string; onPress: () => void }) => (
    <Pressable onPress={onPress}>
      <Card style={{ marginBottom: spacing.sm }}>
        <AppText weight="700" size={14}>
          {label}
        </AppText>
      </Card>
    </Pressable>
  );

  return (
    <Screen>
      <ScreenHeader title={t("profileTitle")} />

      <Card style={{ marginBottom: spacing.lg }}>
        <AppText weight="800" size={17}>
          {name}
        </AppText>
        <AppText muted weight="600" size={13} style={{ marginTop: 2 }}>
          {user?.email}
        </AppText>
      </Card>

      <Row label={t("profileFullStats")} onPress={() => navigate("statistics")} />
      <Row label={t("profilePlanning")} onPress={() => navigate("planning")} />
      <Row label={t("mistakesTitle")} onPress={() => navigate("mistakes")} />
      <Row label={t("uptodateTitle")} onPress={() => navigate("uptodate")} />

      <View style={{ flexDirection: "row", gap: spacing.md, marginTop: spacing.sm }}>
        <Button
          variant="secondary"
          full={false}
          label={isDark ? "☀ Light" : "☾ Dark"}
          onPress={toggleTheme}
          style={{ flex: 1 }}
        />
        <Button
          variant="secondary"
          full={false}
          label={isFa ? "English" : "فارسی"}
          onPress={toggleLang}
          style={{ flex: 1 }}
        />
      </View>

      <Button
        label={t("profileLogout")}
        variant="ghost"
        onPress={signOut}
        style={{ marginTop: spacing.lg }}
      />
    </Screen>
  );
}
