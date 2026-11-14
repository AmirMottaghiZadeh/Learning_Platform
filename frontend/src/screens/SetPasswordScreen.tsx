import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { ApiError } from "@/api/client";
import { authApi } from "@/api/endpoints";
import { AuthLayout } from "@/components/AuthLayout";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Input } from "@/components/primitives/Input";
import { useLang } from "@/i18n/LanguageProvider";
import { useAuth } from "@/store/auth";
import { useTheme } from "@/theme/ThemeProvider";

/** Shown, before anything else, to someone just signed in with an SMS code:
 * right after signing up (no password yet -- name and password are asked
 * for together), or after a forgotten-password code (a new password). Once
 * saved, every later sign-in is mobile number + password, no SMS. */
export function SetPasswordScreen() {
  const { t } = useLang();
  const { colors } = useTheme();
  const user = useAuth((s) => s.user);
  const passwordChosen = useAuth((s) => s.passwordChosen);
  const signOut = useAuth((s) => s.signOut);
  const isNewAccount = !user?.has_password;

  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    if ((isNewAccount && !name.trim()) || !password || !confirm) {
      setError(t("fillRequiredFields"));
      return;
    }
    if (password !== confirm) {
      setError(t("passwordsDontMatch"));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const updated = await authApi.setPassword({
        new_password: password,
        new_password_confirm: confirm,
        ...(isNewAccount ? { name: name.trim() } : {}),
      });
      passwordChosen(updated);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("loadFailed"));
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      title={isNewAccount ? t("setPasswordTitle") : t("newPasswordTitle")}
      subtitle={isNewAccount ? t("setPasswordSubtitle") : t("newPasswordSubtitle")}
    >
      <View style={{ gap: 12 }}>
        {isNewAccount ? (
          <Input placeholder={t("nameLabel")} autoComplete="name" textContentType="name" value={name} onChangeText={setName} />
        ) : null}
        <Input
          placeholder={t("passwordLabel")}
          secureTextEntry
          autoComplete="new-password"
          textContentType="newPassword"
          value={password}
          onChangeText={setPassword}
        />
        <Input
          placeholder={t("passwordConfirmLabel")}
          secureTextEntry
          autoComplete="new-password"
          textContentType="newPassword"
          value={confirm}
          onChangeText={setConfirm}
          onSubmitEditing={save}
        />
      </View>
      <AppText muted weight="600" size={12} style={{ marginTop: 8 }}>
        {t("passwordRule")}
      </AppText>

      {error ? (
        <AppText size={12} weight="700" color={colors.denyLabel} style={{ marginTop: 12 }}>
          {error}
        </AppText>
      ) : null}

      <Button label={t("savePasswordBtn")} onPress={save} loading={busy} style={{ marginTop: 20 }} />
      <Pressable onPress={() => signOut()} style={{ marginTop: 14, alignSelf: "center" }}>
        <AppText muted weight="600" size={13}>
          {t("useAnotherAccount")}
        </AppText>
      </Pressable>
    </AuthLayout>
  );
}
