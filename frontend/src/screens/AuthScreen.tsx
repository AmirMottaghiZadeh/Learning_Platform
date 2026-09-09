import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { authApi } from "@/api/endpoints";
import { ApiError } from "@/api/client";
import { AppShell } from "@/components/AppShell";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { IconImage } from "@/components/primitives/IconImage";
import { Input } from "@/components/primitives/Input";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useAuth } from "@/store/auth";
import { useTheme } from "@/theme/ThemeProvider";
import { radius, spacing } from "@/theme/tokens";

type Mode = "login" | "signup";

export function AuthScreen() {
  const { t, toggle: toggleLang } = useLang();
  const { colors, toggle: toggleTheme, isDark } = useTheme();
  const applyAuth = useAuth((s) => s.applyAuth);

  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const payload =
        mode === "login"
          ? await authApi.login({ username: email.trim(), password })
          : await authApi.register({
              name: name.trim(),
              email: email.trim(),
              password,
              password_confirm: password,
            });
      await applyAuth(payload);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("loadFailed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AppShell>
      <View style={{ flex: 1, backgroundColor: colors.headerMesh }}>
        <View
          style={{
            flexDirection: "row",
            justifyContent: "space-between",
            padding: 18,
          }}
        >
          <Pressable
            onPress={toggleLang}
            style={{
              backgroundColor: colors.onAccentChip,
              borderWidth: 1,
              borderColor: colors.onAccentChipBorder,
              borderRadius: radius.chip,
              paddingHorizontal: 12,
              paddingVertical: 6,
            }}
          >
            <AppText weight="800" size={12} color="#fff">
              {t("langSwitch")}
            </AppText>
          </Pressable>
          <Pressable
            onPress={toggleTheme}
            style={{
              width: 34,
              height: 34,
              borderRadius: 17,
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: colors.onAccentChip,
              borderWidth: 1,
              borderColor: colors.onAccentChipBorder,
            }}
          >
            <AppText size={14} color="#fff">
              {isDark ? "☀" : "☾"}
            </AppText>
          </Pressable>
        </View>

        <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 32 }}>
          <View
            style={{
              width: 88,
              height: 88,
              borderRadius: 26,
              backgroundColor: "#fff",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 20,
            }}
          >
            <IconImage name="mortar" size={56} />
          </View>
          <AppText weight="900" size={26} color="#fff" center>
            {t("appName")}
          </AppText>
          <AppText weight="600" size={14} color={colors.onAccentSub} center style={{ marginTop: 8 }}>
            {t("tagline")}
          </AppText>
        </View>

        <View
          style={{
            backgroundColor: colors.appBg,
            borderTopLeftRadius: 28,
            borderTopRightRadius: 28,
            padding: 26,
          }}
        >
          <Screen scroll={false} padded={false}>
            <AppText weight="800" size={20}>
              {mode === "login" ? t("loginTitle") : t("signupTitle")}
            </AppText>
            <AppText muted weight="600" size={13} style={{ marginBottom: spacing.lg }}>
              {mode === "login" ? t("loginSubtitle") : t("signupSubtitle")}
            </AppText>

            <View style={{ gap: 12 }}>
              {mode === "signup" ? (
                <Input placeholder={t("nameLabel")} value={name} onChangeText={setName} />
              ) : null}
              <Input
                placeholder={t("emailLabel")}
                autoCapitalize="none"
                keyboardType="email-address"
                value={email}
                onChangeText={setEmail}
              />
              <Input
                placeholder={t("passwordLabel")}
                secureTextEntry
                value={password}
                onChangeText={setPassword}
              />
            </View>

            {error ? (
              <AppText size={12} weight="700" color={colors.denyLabel} style={{ marginTop: 10 }}>
                {error}
              </AppText>
            ) : null}

            <Button
              label={mode === "login" ? t("loginBtn") : t("signupBtn")}
              onPress={submit}
              loading={busy}
              style={{ marginTop: 18 }}
            />

            <Pressable
              onPress={() => {
                setMode(mode === "login" ? "signup" : "login");
                setError(null);
              }}
              style={{ marginTop: 14, alignSelf: "center" }}
            >
              <AppText muted weight="600" size={13}>
                {mode === "login" ? t("noAccount") : t("haveAccount")}{" "}
                <AppText weight="800" size={13} color={colors.accent}>
                  {mode === "login" ? t("signupLink") : t("loginLink")}
                </AppText>
              </AppText>
            </Pressable>
          </Screen>
        </View>
      </View>
    </AppShell>
  );
}
