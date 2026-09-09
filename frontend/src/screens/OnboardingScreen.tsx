import React, { useState } from "react";
import { Pressable, ScrollView, View } from "react-native";
import Svg, { Circle, Path, Rect } from "react-native-svg";

import { authApi } from "@/api/endpoints";
import { AppShell } from "@/components/AppShell";
import { HeaderMesh } from "@/components/HeaderMesh";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useAuth } from "@/store/auth";
import { useTheme } from "@/theme/ThemeProvider";

const FIELDS = [
  { v: "pharmacy", fa: "داروسازی", en: "Pharmacy" },
  { v: "medicine", fa: "پزشکی", en: "Medicine" },
  { v: "nursing", fa: "پرستاری", en: "Nursing" },
];
const GOALS = [
  { v: "residency", fa: "آزمون دستیاری", en: "Residency exam" },
  { v: "final", fa: "امتحانات ترم", en: "Term finals" },
  { v: "clinical", fa: "مرور بالینی روزانه", en: "Daily clinical review" },
];
const LEVELS = [
  { v: "beginner", fa: "مبتدی", en: "Beginner" },
  { v: "intermediate", fa: "متوسط", en: "Intermediate" },
  { v: "advanced", fa: "پیشرفته", en: "Advanced" },
];

const SLIDES = [
  {
    fa: { title: "فلش‌کارت + جعبه‌ی لایتنر", desc: "دقیقاً همون داروهایی رو مرور کن که وقتشه فراموش نشن، با تکرار فاصله‌دار هوشمند." },
    en: { title: "Flashcards + Leitner box", desc: "Review exactly the drugs due for review, with smart spaced repetition." },
  },
  {
    fa: { title: "آزمون‌های کوتاه دارویی", desc: "دانشت رو با سوالات چندگزینه‌ای واقعی و بازخورد فوری بسنج." },
    en: { title: "Short pharma quizzes", desc: "Test your knowledge with real multiple-choice questions and instant feedback." },
  },
  {
    fa: { title: "پیشرفت و برنامه‌ریزی", desc: "آمار کامل مطالعه، اشتباهات پرتکرار و برنامه‌ی هفتگی‌ت رو یک‌جا ببین." },
    en: { title: "Progress & planning", desc: "See full study stats, recurring mistakes and your weekly plan in one place." },
  },
];

function SlideIcon({ index }: { index: number }) {
  return (
    <Svg width={44} height={44} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.6}>
      {index === 0 ? (
        <>
          <Rect x={4} y={4} width={16} height={16} rx={3} />
          <Rect x={7} y={7} width={13} height={13} rx={3} />
        </>
      ) : index === 1 ? (
        <>
          <Circle cx={12} cy={12} r={9} />
          <Path d="M9 9h6M9 12h6M9 15h3" strokeLinecap="round" />
        </>
      ) : (
        <Path d="M4 19V10M10 19V5M16 19v-7M22 19H2" strokeLinecap="round" />
      )}
    </Svg>
  );
}

export function OnboardingScreen() {
  const { t, isFa, lang } = useLang();
  const { colors, shadows } = useTheme();
  const setUser = useAuth((s) => s.setUser);

  const [step, setStep] = useState(0);
  const [field, setField] = useState("");
  const [goal, setGoal] = useState("");
  const [level, setLevel] = useState("");
  const [busy, setBusy] = useState(false);

  const isForm = step === 3;
  const formReady = field && goal && level;

  const submit = async () => {
    setBusy(true);
    try {
      setUser(
        await authApi.onboarding({
          study_field: field,
          study_goal: goal,
          study_level: level,
          language: lang,
        }),
      );
    } catch {
      setBusy(false);
    }
  };

  const ChipGroup = ({
    label,
    options,
    value,
    onChange,
  }: {
    label: string;
    options: typeof FIELDS;
    value: string;
    onChange: (v: string) => void;
  }) => (
    <View style={{ marginBottom: 18 }}>
      <AppText weight="800" size={12} color="rgba(255,255,255,0.85)" style={{ marginBottom: 8 }}>
        {label}
      </AppText>
      <View style={{ gap: 8 }}>
        {options.map((o) => {
          const sel = value === o.v;
          return (
            <Pressable
              key={o.v}
              onPress={() => onChange(o.v)}
              style={[
                {
                  paddingVertical: 13,
                  paddingHorizontal: 16,
                  borderRadius: 14,
                  backgroundColor: sel ? colors.accent + "1a" : colors.softBg,
                  borderWidth: 1.5,
                  borderColor: sel ? colors.accent : colors.trackBg,
                },
                !sel && shadows.raisedSm,
              ]}
            >
              <AppText weight={sel ? "800" : "600"} size={14} color={sel ? colors.accent : colors.ink}>
                {isFa ? o.fa : o.en}
              </AppText>
            </Pressable>
          );
        })}
      </View>
    </View>
  );

  return (
    <AppShell>
      <HeaderMesh>
        <View style={{ flexDirection: "row", justifyContent: "flex-end", padding: 22 }}>
          <Pressable
            onPress={submit}
            style={{
              backgroundColor: "rgba(255,255,255,0.16)",
              borderWidth: 1,
              borderColor: "rgba(255,255,255,0.3)",
              borderRadius: 999,
              paddingHorizontal: 13,
              paddingVertical: 6,
            }}
          >
            <AppText weight="700" size={12} color="#fff">
              {t("obSkip")}
            </AppText>
          </Pressable>
        </View>

        {isForm ? (
          <ScrollView
            style={{ flex: 1 }}
            contentContainerStyle={{ paddingHorizontal: 26 }}
            showsVerticalScrollIndicator={false}
          >
            <AppText weight="800" size={20} color="#fff">
              {t("obFormTitle")}
            </AppText>
            <AppText weight="600" size={13} color="rgba(255,255,255,0.78)" style={{ marginBottom: 20, marginTop: 4 }}>
              {t("obFormSub")}
            </AppText>
            <ChipGroup label={t("obFieldLabel")} options={FIELDS} value={field} onChange={setField} />
            <ChipGroup label={t("obGoalLabel")} options={GOALS} value={goal} onChange={setGoal} />
            <ChipGroup label={t("obLevelLabel")} options={LEVELS} value={level} onChange={setLevel} />
          </ScrollView>
        ) : (
          <View style={{ flex: 1, alignItems: "center", justifyContent: "center", paddingHorizontal: 30 }}>
            <View
              style={{
                width: 92,
                height: 92,
                borderRadius: 26,
                backgroundColor: "rgba(255,255,255,0.14)",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: 26,
              }}
            >
              <SlideIcon index={step} />
            </View>
            <AppText weight="800" size={20} color="#fff" center style={{ marginBottom: 10 }}>
              {SLIDES[step][lang].title}
            </AppText>
            <AppText
              weight="600"
              size={14}
              color="rgba(255,255,255,0.82)"
              center
              style={{ lineHeight: 27, maxWidth: 270 }}
            >
              {SLIDES[step][lang].desc}
            </AppText>
          </View>
        )}

        <View style={{ paddingHorizontal: 26, paddingTop: 18, paddingBottom: 30, gap: 16 }}>
          <View style={{ flexDirection: "row", gap: 6, justifyContent: "center" }}>
            {[0, 1, 2, 3].map((i) => (
              <View
                key={i}
                style={{
                  width: i === step ? 22 : 5,
                  height: 5,
                  borderRadius: 3,
                  backgroundColor: i === step ? "#fff" : "rgba(255,255,255,0.34)",
                }}
              />
            ))}
          </View>
          <View style={{ flexDirection: "row", gap: 10 }}>
            {step > 0 ? (
              <Pressable
                onPress={() => setStep(step - 1)}
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 16,
                  alignItems: "center",
                  justifyContent: "center",
                  backgroundColor: "rgba(255,255,255,0.18)",
                  borderWidth: 1.5,
                  borderColor: "rgba(255,255,255,0.4)",
                }}
              >
                <AppText weight="800" size={16} color="#fff">
                  {isFa ? "›" : "‹"}
                </AppText>
              </Pressable>
            ) : null}
            <Pressable
              onPress={() => (isForm ? submit() : setStep(step + 1))}
              disabled={isForm ? !formReady || busy : false}
              style={{
                flex: 1,
                height: 52,
                borderRadius: 16,
                alignItems: "center",
                justifyContent: "center",
                opacity: isForm && !formReady ? 0.55 : 1,
                backgroundColor: isForm ? "#fff" : "rgba(255,255,255,0.18)",
                borderWidth: isForm ? 0 : 1.5,
                borderColor: "rgba(255,255,255,0.4)",
              }}
            >
              <AppText weight="800" size={15} color={isForm ? "#16241F" : "#fff"}>
                {isForm ? t("obStart") : t("obNext")}
              </AppText>
            </Pressable>
          </View>
        </View>
      </HeaderMesh>
    </AppShell>
  );
}
