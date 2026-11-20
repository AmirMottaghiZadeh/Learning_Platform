import React, { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, View } from "react-native";
import Svg, { Path } from "react-native-svg";
import { aiLabApi } from "@/api/aiLab";
import { useTheme } from "@/theme/ThemeProvider";
import { useLang } from "@/i18n/LanguageProvider";
import { AppText } from "@/components/primitives/AppText";

function Thumb({ down, color }: { down: boolean; color: string }) {
  return <Svg width={21} height={21} viewBox="0 0 24 24" style={down ? { transform: [{ rotate: "180deg" }] } : undefined}>
    <Path d="M7 10v11H3V10h4Zm0 0 5-8c2 0 3 2 2.5 4L14 9h5a2 2 0 0 1 2 2.4l-1.4 7a3 3 0 0 1-3 2.6H7" fill="none" stroke={color} strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" />
  </Svg>;
}

export function SearchFeedback({ jobId, available }: { jobId: string; available: boolean }) {
  const { colors } = useTheme();
  const { row, isFa } = useLang();
  const [vote, setVote] = useState<1 | -1 | null>(null);
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let stopped = false;
    setVote(null); setError(""); setLoaded(false);
    if (available) void aiLabApi.feedback(jobId).then(result => { if (!stopped) setVote(result.value); })
      .catch(() => { if (!stopped) setError(isFa ? "دریافت بازخورد قبلی ممکن نشد؛ دوباره تلاش کنید." : "Could not load your feedback. Please try again."); })
      .finally(() => { if (!stopped) setLoaded(true); });
    return () => { stopped = true; };
  }, [jobId, available, isFa]);
  const rate = async (value: 1 | -1) => {
    if (busy) return;
    setBusy(true); setError("");
    try { const result = await aiLabApi.rate(jobId, value); setVote(result.value); }
    catch { setError(isFa ? "بازخورد ذخیره نشد؛ دوباره تلاش کنید." : "Feedback was not saved. Please try again."); }
    finally { setBusy(false); }
  };
  return <View testID="reference-feedback" style={{ padding: 14, gap: 12, borderRadius: 16, backgroundColor: colors.softBg }}>
    <AppText size={13} weight="700">{isFa ? "آیا پاسخ دریافتی درست و مرتبط با سؤال شما بود؟" : "Did this answer your question correctly?"}</AppText>
    <View style={{ flexDirection: row, alignItems: "center", gap: 10 }}>
      {([1, -1] as const).map(value => {
        const selected = vote === value;
        const color = selected ? colors.onAccent : colors.accent;
        return <Pressable key={value} testID={value === 1 ? "reference-like" : "reference-dislike"} accessibilityRole="button"
          accessibilityLabel={isFa ? (value === 1 ? "پاسخ درست و مفید بود" : "پاسخ درست یا کافی نبود") : value === 1 ? "Helpful answer" : "Incorrect or incomplete answer"}
          accessibilityState={{ selected, disabled: !available || busy || (!loaded && !error) }} disabled={!available || busy || (!loaded && !error)} onPress={() => void rate(value)}
          style={{ minWidth: 92, minHeight: 46, paddingHorizontal: 14, flexDirection: row, gap: 8, alignItems: "center", justifyContent: "center", borderRadius: 12,
            borderWidth: 1, borderColor: colors.accent, backgroundColor: selected ? colors.accent : colors.cardBg, opacity: !available || busy ? 0.5 : 1 }}>
          <Thumb down={value === -1} color={color} /><AppText size={13} color={color}>{isFa ? (value === 1 ? "بله" : "خیر") : value === 1 ? "Yes" : "No"}</AppText>
        </Pressable>;
      })}
      {available && (busy || (!loaded && !error)) ? <ActivityIndicator size="small" color={colors.accent} /> : null}
    </View>
    {!available ? <AppText size={12} muted>{isFa ? "ثبت بازخورد برای این پاسخ فعلاً در دسترس نیست." : "Feedback is currently unavailable for this answer."}</AppText> : null}
    {vote !== null ? <AppText size={12} color={colors.accent} accessibilityLiveRegion="polite">{isFa ? "بازخورد شما ثبت شد. می‌توانید نظرتان را تغییر دهید." : "Feedback saved. You can change your rating."}</AppText> : null}
    {error ? <AppText size={12} color={colors.denyLabel} accessibilityLiveRegion="polite">{error}</AppText> : null}
  </View>;
}
