import React, { useState } from "react";
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, View } from "react-native";

import { ApiError } from "@/api/client";
import { authApi } from "@/api/endpoints";
import { AppShell } from "@/components/AppShell";
import { GlassToggles } from "@/components/GlassToggles";
import { HeaderMesh } from "@/components/HeaderMesh";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { IconImage } from "@/components/primitives/IconImage";
import { Input } from "@/components/primitives/Input";
import { useLang } from "@/i18n/LanguageProvider";
import { useAuth } from "@/store/auth";
import { useTheme } from "@/theme/ThemeProvider";

type Mode = "login" | "signup";

export function AuthScreen() {
  const { t } = useLang();
  const { colors } = useTheme();
  const applyAuth = useAuth((s) => s.applyAuth);

  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isSignup = mode === "signup";

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const payload = isSignup
        ? await authApi.register({
            name: name.trim(),
            email: email.trim(),
            password,
            password_confirm: password,
          })
        : await authApi.login({ username: email.trim(), password });
      await applyAuth(payload);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("loadFailed"));
      setBusy(false);
    }
  };

  return (
    <AppShell>
      <HeaderMesh>
        <KeyboardAvoidingView
          behavior={Platform.OS === "ios" ? "padding" : undefined}
          style={{ flex: 1 }}
        >
          <GlassToggles />

          <View
            style={{ flex: 1, alignItems: "center", justifyContent: "center", paddingHorizontal: 32 }}
          >
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
            {/* The header mesh is a dark teal gradient in BOTH themes, so this
                text must stay light — `onAccentSub` flips to near-black in dark
                mode (it is tuned for text on the light accent pill). */}
            <AppText
              weight="600"
              size={14}
              color="rgba(255,255,255,0.85)"
              center
              style={{ marginTop: 8 }}
            >
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
                {isSignup ? t("signupTitle") : t("loginTitle")}
              </AppText>
              <AppText muted weight="600" size={13} style={{ marginTop: 4, marginBottom: 20 }}>
                {isSignup ? t("signupSubtitle") : t("loginSubtitle")}
              </AppText>

              <View style={{ gap: 12 }}>
                {isSignup ? (
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
                <AppText size={12} weight="700" color={colors.denyLabel} style={{ marginTop: 12 }}>
                  {error}
                </AppText>
              ) : null}

              <Button
                label={isSignup ? t("signupBtn") : t("loginBtn")}
                onPress={submit}
                loading={busy}
                style={{ marginTop: 20 }}
              />

              {isSignup ? (
                <AppText muted weight="600" size={12} center style={{ marginTop: 12, lineHeight: 20 }}>
                  {t("signupTerms")}
                </AppText>
              ) : null}

              <Pressable
                onPress={() => {
                  setMode(isSignup ? "login" : "signup");
                  setError(null);
                }}
                style={{ marginTop: 14, alignSelf: "center" }}
              >
                <AppText muted weight="600" size={13}>
                  {isSignup ? t("haveAccount") : t("noAccount")}{" "}
                  <AppText weight="800" size={13} color={colors.accent}>
                    {isSignup ? t("loginLink") : t("signupLink")}
                  </AppText>
                </AppText>
              </Pressable>
            </ScrollView>
          </View>
        </KeyboardAvoidingView>
      </HeaderMesh>
    </AppShell>
  );
}
