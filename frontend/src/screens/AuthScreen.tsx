import React, { useEffect, useState } from "react";
import { Platform, Pressable, View } from "react-native";

import { ApiError } from "@/api/client";
import { authApi } from "@/api/endpoints";
import { OtpPurpose } from "@/api/types";
import { AuthLayout } from "@/components/AuthLayout";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Input } from "@/components/primitives/Input";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";
import { useAuth } from "@/store/auth";
import { useTheme } from "@/theme/ThemeProvider";

type Mode = "login" | "signup" | "reset";
type Step = "phone" | "code";

/** Signed-out entry. Three paths:
 * - login: mobile number (or an old account's email) + password, no SMS;
 * - signup: mobile number -> SMS code -> signed in; the app then asks for a
 *   password (SetPasswordScreen) before anything else;
 * - reset (forgotten password): mobile number -> SMS code -> signed in,
 *   then a new password. */
export function AuthScreen() {
  const { t, n, row } = useLang();
  const { colors } = useTheme();
  const applyAuth = useAuth((s) => s.applyAuth);

  const [mode, setMode] = useState<Mode>("login");
  const [step, setStep] = useState<Step>("phone");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [codeLength, setCodeLength] = useState(5);
  const [sentTo, setSentTo] = useState("");
  const [countdown, setCountdown] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const purpose: OtpPurpose = mode === "reset" ? "reset" : "signup";

  const switchTo = (next: Mode) => {
    setMode(next);
    setStep("phone");
    setCode("");
    setError(null);
  };
  useBackInterceptor(mode !== "login", () => (step === "code" ? setStep("phone") : switchTo("login")));

  useEffect(() => {
    if (countdown <= 0) return;
    const id = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(id);
  }, [countdown]);

  const messageFor = (e: unknown) => {
    if (e instanceof ApiError) {
      if (e.code === "INVALID_CREDENTIALS") return t("invalidCredentials");
      // The server's own messages for these flows are already user-facing Persian.
      return e.message;
    }
    return t("loadFailed");
  };

  const run = async (work: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await work();
    } catch (e) {
      setError(messageFor(e));
    } finally {
      setBusy(false);
    }
  };

  const login = () => {
    // Autofill can fill a field without firing onChangeText (RN-web +
    // password managers), leaving state blank while the field shows text.
    if (!identifier.trim() || !password) {
      setError(t("fillRequiredFields"));
      return;
    }
    run(async () => {
      await applyAuth(await authApi.login({ username: identifier.trim(), password }));
    });
  };

  const sendCode = () => {
    if (!phone.trim()) {
      setError(t("fillRequiredFields"));
      return;
    }
    run(async () => {
      try {
        const sent = await authApi.requestOtp({ phone: phone.trim(), purpose });
        setSentTo(sent.phone);
        setCodeLength(sent.code_length);
        setCountdown(sent.resend_in);
        setCode("");
        setStep("code");
      } catch (e) {
        if (e instanceof ApiError && e.code === "OTP_TOO_SOON") {
          // A code was sent moments ago (e.g. the number was edited back to
          // the same one) -- it still works, so go enter it.
          const wait = (e.details as { retry_after?: number })?.retry_after ?? 0;
          setCountdown(wait);
          setSentTo(phone.trim());
          setStep("code");
          return;
        }
        if (e instanceof ApiError && e.code === "PHONE_REGISTERED") {
          // Already has an account: send them to sign in with this number.
          setMode("login");
          setIdentifier(phone.trim());
        }
        throw e;
      }
    });
  };

  const verify = (value = code) => {
    if (value.length < codeLength) return;
    run(async () => {
      const payload = await authApi.verifyOtp({ phone: sentTo || phone.trim(), purpose, code: value });
      await applyAuth(payload, { mustSetPassword: purpose === "reset" });
    });
  };

  const onCode = (value: string) => {
    const digits = value.replace(/[۰-۹]/g, (d) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(d))).replace(/\D/g, "");
    setCode(digits.slice(0, codeLength));
    if (digits.length === codeLength && !busy) verify(digits.slice(0, codeLength));
  };

  const title = mode === "login" ? t("loginTitle") : mode === "signup" ? t("signupTitle") : t("resetTitle");
  const subtitle =
    step === "code" && mode !== "login"
      ? t("otpSubtitle").replace("{n}", n(codeLength)).replace("{phone}", n(sentTo))
      : mode === "login"
        ? t("loginSubtitle")
        : mode === "signup"
          ? t("phoneSignupSubtitle")
          : t("resetSubtitle");

  return (
    <AuthLayout title={step === "code" && mode !== "login" ? t("otpTitle") : title} subtitle={subtitle}>
      {mode === "login" ? (
        <View style={{ gap: 12 }}>
          <Input
            placeholder={t("phoneOrEmailLabel")}
            autoCapitalize="none"
            autoComplete="username"
            textContentType="username"
            value={identifier}
            onChangeText={setIdentifier}
          />
          <Input
            placeholder={t("passwordLabel")}
            secureTextEntry
            autoComplete="current-password"
            textContentType="password"
            value={password}
            onChangeText={setPassword}
            onSubmitEditing={login}
          />
        </View>
      ) : step === "phone" ? (
        <Input
          placeholder={t("phoneLabel")}
          keyboardType="phone-pad"
          autoComplete="tel"
          textContentType="telephoneNumber"
          value={phone}
          onChangeText={setPhone}
          onSubmitEditing={sendCode}
          autoFocus
        />
      ) : (
        <Input
          placeholder={t("otpPlaceholder")}
          keyboardType="number-pad"
          // Lets the phone or browser offer the code straight from the SMS.
          autoComplete={Platform.OS === "web" ? ("one-time-code" as never) : "sms-otp"}
          textContentType="oneTimeCode"
          maxLength={codeLength}
          value={code}
          onChangeText={onCode}
          autoFocus
          style={{ textAlign: "center", letterSpacing: 8, fontSize: 20, writingDirection: "ltr" }}
        />
      )}

      {error ? (
        <AppText size={12} weight="700" color={colors.denyLabel} style={{ marginTop: 12 }}>
          {error}
        </AppText>
      ) : null}

      {mode === "login" ? (
        <>
          <Button label={t("loginBtn")} onPress={login} loading={busy} style={{ marginTop: 20 }} />
          <Pressable onPress={() => switchTo("reset")} style={{ marginTop: 14, alignSelf: "center" }}>
            <AppText weight="700" size={13} color={colors.accent}>
              {t("forgotPassword")}
            </AppText>
          </Pressable>
        </>
      ) : step === "phone" ? (
        <Button label={t("sendCodeBtn")} onPress={sendCode} loading={busy} style={{ marginTop: 20 }} />
      ) : (
        <>
          <Button
            label={t("verifyBtn")}
            onPress={() => verify()}
            loading={busy}
            disabled={code.length < codeLength}
            style={{ marginTop: 20 }}
          />
          <View style={{ flexDirection: row, justifyContent: "space-between", marginTop: 14 }}>
            <Pressable onPress={() => setStep("phone")} hitSlop={8}>
              <AppText weight="700" size={13} color={colors.accent}>
                {t("editPhone")}
              </AppText>
            </Pressable>
            {countdown > 0 ? (
              <AppText muted weight="600" size={13}>
                {t("resendIn").replace("{s}", n(countdown))}
              </AppText>
            ) : (
              <Pressable onPress={sendCode} disabled={busy} hitSlop={8}>
                <AppText weight="700" size={13} color={colors.accent}>
                  {t("resendCode")}
                </AppText>
              </Pressable>
            )}
          </View>
        </>
      )}

      {mode === "signup" && step === "phone" ? (
        <AppText muted weight="600" size={12} center style={{ marginTop: 12, lineHeight: 20 }}>
          {t("signupTerms")}
        </AppText>
      ) : null}

      <Pressable
        onPress={() => switchTo(mode === "login" ? "signup" : "login")}
        style={{ marginTop: 14, alignSelf: "center" }}
      >
        <AppText muted weight="600" size={13}>
          {mode === "login" ? t("noAccount") : t("haveAccount")}{" "}
          <AppText weight="800" size={13} color={colors.accent}>
            {mode === "login" ? t("signupLink") : t("loginLink")}
          </AppText>
        </AppText>
      </Pressable>
    </AuthLayout>
  );
}
