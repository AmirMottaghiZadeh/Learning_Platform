import React, {useState} from "react";
import {Pressable, StyleSheet, Text, TextInput, View} from "react-native";
import {KeyRound, LogIn, UserPlus} from "lucide-react-native";
import {useMutation} from "@tanstack/react-query";

import {API_BASE_URL} from "../api/client";
import {platformApi} from "../api/platform";
import {LearningCard, PrimaryButton, SecondaryButton} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";

export function AuthScreen() {
  const {signIn, register, loading, error} = useAuth();
  const [mode, setMode] = useState<"login" | "register" | "forgot">("login");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  const resetMutation = useMutation({
    mutationFn: () => platformApi.requestPasswordReset(email.trim()),
    onSuccess: (response) => {
      setResetMessage(response.message);
      setLocalError(null);
    },
    onError: (exc) => {
      setLocalError(exc instanceof Error ? exc.message : "درخواست بازیابی رمز با خطا مواجه شد.");
    },
  });

  async function submit() {
    setLocalError(null);
    setResetMessage(null);
    if (mode === "forgot") {
      if (!email.trim()) {
        setLocalError("ایمیل برای بازیابی کلمه عبور الزامی است.");
        return;
      }
      resetMutation.mutate();
      return;
    }
    if (!username.trim() || !password.trim()) {
      setLocalError("نام کاربری و رمز عبور الزامی است.");
      return;
    }
    if (mode === "register") {
      if (!firstName.trim() || !lastName.trim() || !email.trim()) {
        setLocalError("نام، نام خانوادگی و ایمیل الزامی است.");
        return;
      }
      if (password !== passwordConfirm) {
        setLocalError("کلمه عبور و تکرار آن یکسان نیست.");
        return;
      }
    }
    try {
      if (mode === "login") {
        await signIn(username.trim(), password);
      } else {
        await register({
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          username: username.trim(),
          email: email.trim(),
          password,
          password_confirm: passwordConfirm,
        });
      }
    } catch {
      // AuthProvider exposes the message.
    }
  }

  return (
    <View style={styles.root}>
      <View style={styles.brand}>
        <Text style={styles.brandMark}>K</Text>
        <View>
          <Text style={styles.brandTitle}>Pharmexa</Text>
          <Text style={styles.brandSubtitle}>پلتفرم یادگیری</Text>
        </View>
      </View>

      <LearningCard tone="mint">
        <View style={styles.segment}>
          <Pressable
            accessibilityRole="button"
            onPress={() => setMode("login")}
            style={[styles.segmentItem, mode === "login" && styles.segmentActive]}
          >
            <Text style={[styles.segmentText, mode === "login" && styles.segmentTextActive]}>ورود</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            onPress={() => setMode("register")}
            style={[styles.segmentItem, mode === "register" && styles.segmentActive]}
          >
            <Text style={[styles.segmentText, mode === "register" && styles.segmentTextActive]}>ثبت‌نام</Text>
          </Pressable>
        </View>

        {mode === "register" ? (
          <>
            <TextInput
              value={firstName}
              onChangeText={setFirstName}
              placeholder="نام"
              placeholderTextColor={colors.softText}
              style={styles.input}
            />
            <TextInput
              value={lastName}
              onChangeText={setLastName}
              placeholder="نام خانوادگی"
              placeholderTextColor={colors.softText}
              style={styles.input}
            />
          </>
        ) : null}
        {mode !== "forgot" ? (
          <TextInput
            autoCapitalize="none"
            value={username}
            onChangeText={setUsername}
            placeholder="نام کاربری"
            placeholderTextColor={colors.softText}
            style={styles.input}
          />
        ) : null}
        {(mode === "register" || mode === "forgot") ? (
          <TextInput
            autoCapitalize="none"
            keyboardType="email-address"
            value={email}
            onChangeText={setEmail}
            placeholder="ایمیل"
            placeholderTextColor={colors.softText}
            style={styles.input}
          />
        ) : null}
        {mode !== "forgot" ? (
          <>
            <TextInput
              secureTextEntry
              value={password}
              onChangeText={setPassword}
              placeholder="کلمه عبور"
              placeholderTextColor={colors.softText}
              style={styles.input}
            />
            {mode === "register" ? (
              <TextInput
                secureTextEntry
                value={passwordConfirm}
                onChangeText={setPasswordConfirm}
                placeholder="تکرار کلمه عبور"
                placeholderTextColor={colors.softText}
                style={styles.input}
              />
            ) : null}
          </>
        ) : null}

        {localError || error ? <Text style={styles.error}>{localError ?? error}</Text> : null}
        {resetMessage ? <Text style={styles.success}>{resetMessage}</Text> : null}

        <PrimaryButton
          label={mode === "login" ? "ورود" : mode === "register" ? "ایجاد حساب" : "ارسال درخواست بازیابی"}
          Icon={mode === "login" ? LogIn : mode === "register" ? UserPlus : KeyRound}
          onPress={submit}
          disabled={loading || resetMutation.isPending}
        />
        {mode === "login" ? (
          <Pressable accessibilityRole="button" onPress={() => setMode("forgot")} style={styles.forgotLink}>
            <Text style={styles.forgotText}>فراموشی کلمه عبور</Text>
          </Pressable>
        ) : null}
        {mode === "forgot" ? (
          <View style={styles.backToLogin}>
            <SecondaryButton label="بازگشت به ورود" onPress={() => setMode("login")} />
          </View>
        ) : null}
      </LearningCard>

      <Text style={styles.apiText}>سرور: {API_BASE_URL}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.background,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xxl,
    justifyContent: "center",
  },
  brand: {
    width: "100%",
    maxWidth: 520,
    alignSelf: "center",
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.xl,
  },
  brandMark: {
    width: 58,
    height: 58,
    borderRadius: radius.lg,
    backgroundColor: colors.primary,
    color: colors.black,
    fontSize: 34,
    fontWeight: "900",
    textAlign: "center",
    lineHeight: 58,
    marginRight: spacing.md,
  },
  brandTitle: {
    color: colors.ink,
    fontSize: typography.title,
    fontWeight: "900",
  },
  brandSubtitle: {
    color: colors.muted,
    fontSize: typography.body,
    fontWeight: "700",
  },
  segment: {
    minHeight: 46,
    flexDirection: "row",
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.pill,
    padding: spacing.xs,
    marginBottom: spacing.lg,
  },
  segmentItem: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.pill,
  },
  segmentActive: {
    backgroundColor: colors.primary,
  },
  segmentText: {
    color: colors.muted,
    fontWeight: "900",
  },
  segmentTextActive: {
    color: colors.black,
  },
  forgotLink: {
    alignSelf: "center",
    marginTop: spacing.md,
    paddingVertical: spacing.sm,
  },
  forgotText: {
    color: colors.primary,
    fontWeight: "900",
  },
  backToLogin: {
    marginTop: spacing.md,
  },
  input: {
    minHeight: 50,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "700",
    paddingHorizontal: spacing.lg,
    marginBottom: spacing.md,
    textAlign: "right",
  },
  error: {
    color: colors.danger,
    fontWeight: "800",
    marginBottom: spacing.md,
  },
  success: {
    color: colors.success,
    fontWeight: "800",
    marginBottom: spacing.md,
    lineHeight: 22,
    textAlign: "right",
  },
  apiText: {
    color: colors.softText,
    fontSize: typography.small,
    textAlign: "center",
    marginTop: spacing.md,
  },
});
