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
    // Browser/OS autofill can fill the visible field without ever firing
    // onChangeText (a well-known RN-web + password-manager quirk), leaving
    // this state stuck at "" while the screen shows it as filled — the
    // server then rejects the blank field and the raw English "Validation
    // error." shows up out of nowhere. Catch it here with a translated
    // message instead of round-tripping to the API to find out.
    const trimmedName = name.trim();
    const trimmedEmail = email.trim();
    if ((isSignup && !trimmedName) || !trimmedEmail || !password) {
      setError(t("fillRequiredFields"));
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const payload = isSignup
        ? await authApi.register({
            name: trimmedName,
            email: trimmedEmail,
            password,
            password_confirm: password,
          })
        : await authApi.login({ username: trimmedEmail, password });
      await applyAuth(payload);
    } catch (e) {
      if (e instanceof ApiError) {
        // INVALID covers a grab-bag of distinct server-side reasons (taken
        // email/username, password too similar to it, mismatched
        // confirmation, too short, too common...) -- show the real message
        // instead of guessing at one, so the actual cause is visible.
        setError(e.code === "INVALID_CREDENTIALS" ? t("invalidCredentials") : e.message);
      } else {
        setError(t("loadFailed"));
      }
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
                  <Input
                    placeholder={t("nameLabel")}
                    autoComplete="name"
                    textContentType="name"
                    value={name}
                    onChangeText={setName}
                  />
                ) : null}
                <Input
                  placeholder={t("emailLabel")}
                  autoCapitalize="none"
                  keyboardType="email-address"
                  autoComplete="email"
                  textContentType="emailAddress"
                  value={email}
                  onChangeText={setEmail}
                />
                <Input
                  placeholder={t("passwordLabel")}
                  secureTextEntry
                  autoComplete={isSignup ? "new-password" : "current-password"}
                  textContentType={isSignup ? "newPassword" : "password"}
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
