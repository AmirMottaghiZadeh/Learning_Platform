import React, { useEffect, useState } from "react";
import { Pressable, View } from "react-native";
import { ApiError } from "@/api/client";
import { authApi } from "@/api/endpoints";
import { AuthLayout } from "@/components/AuthLayout";
import { AuthMethodSelector } from "@/components/AuthMethodSelector";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { OtpInput } from "@/components/OtpInput";
import { Input } from "@/components/primitives/Input";
import { LegalSheet, LegalSlug } from "@/components/LegalSheet";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";
import { useAuth } from "@/store/auth";
import { useTheme } from "@/theme/ThemeProvider";

export function EmailOtpForm({ onBack,mode="login" }: { onBack: () => void;mode?:"login"|"signup" }) {
  const { isFa, n, row, t } = useLang();
  const { colors } = useTheme();
  const applyAuth = useAuth(s => s.applyAuth);
  const [email,setEmail]=useState("");const [sent,setSent]=useState("");const [code,setCode]=useState("");
  const [length,setLength]=useState(6);const [wait,setWait]=useState(0);const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");const [legal,setLegal]=useState<LegalSlug|null>(null);
  useBackInterceptor(true,() => sent ? setSent("") : onBack());
  useEffect(() => { if(wait>0){const id=setTimeout(() => setWait(v => v-1),1000);return () => clearTimeout(id);} },[wait]);
  const run=async(work:() => Promise<void>) => {setBusy(true);setError("");try{await work();}catch(e){setError(e instanceof ApiError ? e.message : t("loadFailed"));}finally{setBusy(false);}};
  const request=() => {
    const target=email.trim().toLowerCase();
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(target)){setError(isFa ? "یک نشانی ایمیل معتبر وارد کنید." : "Enter a valid email address.");return;}
    void run(async() => {const data=await authApi.requestEmailOtp(target);setSent(data.email);setLength(data.code_length);setWait(data.resend_in);setCode("");});
  };
  const verify = () => {
    if (busy || code.length !== length) return;
    void run(async () => { await applyAuth(await authApi.verifyEmailOtp(sent, code)); });
  };
  return <AuthLayout panel compact={!!sent} title={sent ? isFa ? "کد ورود ایمیلی" : "Email verification code" : mode==="signup" ? isFa?"ساخت حساب با ایمیل":"Create an account with email" : isFa ? "ورود با ایمیل" : "Sign in with email"}
    subtitle={sent ? isFa ? `کد ${n(length)} رقمی به ${sent} فرستاده شد؛ پوشهٔ هرزنامه را هم بررسی کنید.` : `We sent a ${length}-digit code to ${sent}. Check your spam folder too.`
      : isFa ? "ایمیل خود را وارد کنید تا کد ورود برایتان فرستاده شود. حساب تازه پس از تأیید ایمیل ساخته می‌شود." : "Enter your email to receive a sign-in code. New accounts are created after verification."}>
    {!sent ? <AuthMethodSelector value="email" onChange={method=>{if(method==="mobile")onBack();}} /> : null}
    {sent ? <OtpInput value={code} length={length} onChangeText={setCode} onSubmitEditing={verify} hasError={!!error} />
      : <View style={{ gap: 8 }}>
        <AppText size={14} weight="600">{isFa ? "ایمیل" : "Email"}</AppText>
        <Input value={email} onChangeText={setEmail} accessibilityLabel={isFa ? "ایمیل" : "Email"} keyboardType="email-address"
          autoCapitalize="none" autoComplete="email" placeholder="name@example.com" style={{ writingDirection: "ltr" }} />
      </View>}
    {error ? <AppText nativeID={sent ? "otp-error" : undefined} accessibilityRole="alert" size={13} color={colors.denyLabel} style={{marginTop:8}}>{error}</AppText> : null}
    <Button label={sent ? isFa ? "تأیید و ورود" : "Verify and sign in" : isFa ? "ارسال کد به ایمیل" : "Email me a code"} loading={busy} disabled={!!sent && code.length!==length}
      onPress={sent ? verify : request} style={{marginTop:20}} />
    {sent ? <View style={{flexDirection:row,justifyContent:"space-between",alignItems:"center",marginTop:12}}>
      <Pressable accessibilityRole="button" style={{ minHeight:44, justifyContent:"center" }} onPress={() => {setSent("");setCode("");setError("");}}> <AppText color={colors.accent} size={13}>{isFa ? "ویرایش ایمیل" : "Edit email"}</AppText></Pressable>
      {wait>0 ? <AppText muted size={12}>{isFa ? `ارسال دوباره تا ${n(wait)} ثانیه` : `Resend in ${wait}s`}</AppText> : <Pressable accessibilityRole="button" style={{ minHeight:44, justifyContent:"center" }} disabled={busy} onPress={request}><AppText color={colors.accent} size={13}>{isFa ? "ارسال دوباره" : "Resend code"}</AppText></Pressable>}
    </View> : <AppText muted size={11} style={{marginTop:16,lineHeight:22}}>{isFa ? "با ادامه، " : "By continuing, you accept the "}<AppText color={colors.accent} onPress={() => setLegal("terms")}>{t("termsLink")}</AppText>{isFa ? " و " : " and "}<AppText color={colors.accent} onPress={() => setLegal("privacy")}>{t("privacyLink")}</AppText>{isFa ? " فارمنتا را می‌پذیرید." : "."}</AppText>}
    <Pressable accessibilityRole="button" onPress={onBack} style={{paddingVertical:14,alignItems:"center",marginTop:12}}><AppText color={colors.accent} weight="800">{isFa ? "ورود یا ثبت‌نام با موبایل" : "Use mobile number instead"}</AppText></Pressable>
    <LegalSheet slug={legal} onClose={() => setLegal(null)} />
  </AuthLayout>;
}
