import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { Pressable, ScrollView, View } from "react-native";
import Svg, { Path } from "react-native-svg";

import { authApi, lessonsApi } from "@/api/endpoints";
import { AppShell } from "@/components/AppShell";
import { CategoryPicker, ExamDatePicker, MinutesPicker, StudyDaysPicker } from "@/components/plan/PlanPickers";
import { AppText } from "@/components/primitives/AppText";
import { IconImage, IconName } from "@/components/primitives/IconImage";
import { useLang } from "@/i18n/LanguageProvider";
import { useAuth } from "@/store/auth";
import { useTheme } from "@/theme/ThemeProvider";
import { groupByCategory } from "@/utils/lessonCategories";
import { formatDay, daysUntil } from "@/utils/planDates";

type Option = {
  v: string;
  fa: string;
  en: string;
  descFa: string;
  descEn: string;
  icon?: IconName;
};

const FIELDS: Option[] = [
  {
    v: "pharmacy",
    fa: "داروسازی",
    en: "Pharmacy",
    descFa: "درسنامه‌ی داروها، ATC و تداخلات",
    descEn: "Drug lessons, ATC and interactions",
    icon: "edu-lessons",
  },
  {
    v: "medicine",
    fa: "پزشکی",
    en: "Medicine",
    descFa: "بیماری‌ها، گایدلاین‌ها و ماشین‌حساب‌ها",
    descEn: "Diseases, guidelines and calculators",
    icon: "entry-diseases",
  },
];
const GOALS: Option[] = [
  {
    v: "comprehensive",
    fa: "آزمون پایان دوره",
    en: "End-of-course exam",
    descFa: "مرور جامع برای آزمون پایان دوره",
    descEn: "A full review for the end-of-course exam",
    icon: "entry-education",
  },
  {
    v: "final",
    fa: "امتحانات ترم",
    en: "Term finals",
    descFa: "تمرکز روی درس‌های همین ترم",
    descEn: "Focus on this term's courses",
    icon: "entry-next-chapter",
  },
  {
    v: "clinical",
    fa: "مرور بالینی روزانه",
    en: "Daily clinical review",
    descFa: "مرجع سریع و مرور کوتاه هر روز",
    descEn: "A quick reference and a short daily review",
    icon: "entry-guidelines",
  },
];
const LEVELS: Option[] = [
  {
    v: "beginner",
    fa: "مبتدی",
    en: "Beginner",
    descFa: "تازه با داروها آشنا می‌شم",
    descEn: "Just getting started with drugs",
  },
  {
    v: "intermediate",
    fa: "متوسط",
    en: "Intermediate",
    descFa: "مبانی رو بلدم، دنبال تسلط بیشترم",
    descEn: "I know the basics and want more depth",
  },
  {
    v: "advanced",
    fa: "پیشرفته",
    en: "Advanced",
    descFa: "دنبال جزئیات و نکات تخصصی‌ام",
    descEn: "I'm after the fine detail",
  },
];

type Answers = { field: string; goal: string; level: string };

const QUESTIONS: {
  key: keyof Answers;
  options: Option[];
  fa: { title: string; sub: string };
  en: { title: string; sub: string };
}[] = [
  {
    key: "field",
    options: FIELDS,
    fa: { title: "رشته‌ی تحصیلی‌ات چیه؟", sub: "بخش‌هایی که برای شروع پیشنهاد می‌شن بر اساس رشته‌ات انتخاب می‌شن." },
    en: { title: "What do you study?", sub: "The sections suggested to start with follow it." },
  },
  {
    key: "goal",
    options: GOALS,
    fa: { title: "هدف اصلیت چیه؟", sub: "پیشنهادها و برنامه‌ی مطالعه بر اساس هدفت تنظیم می‌شه." },
    en: { title: "What's your main goal?", sub: "Suggestions and your study plan follow your goal." },
  },
  {
    key: "level",
    options: LEVELS,
    fa: { title: "الان در چه سطحی هستی؟", sub: "سرعت برنامه‌ی مطالعه‌ات با سطحت تنظیم می‌شه." },
    en: { title: "Where are you right now?", sub: "Your study plan's pace follows your level." },
  },
];

// After the three questions: the study plan step, then the summary.
const PLAN_STEP = QUESTIONS.length;
const SUMMARY_STEP = QUESTIONS.length + 1;
const MINUTES = [15, 30, 45, 60, 90];
const CLINICAL_MINUTES = [10, 15, 20, 30];
const WEEKDAYS = [true, true, true, true, true, false, false]; // Saturday to Wednesday

type PlanAnswers = { exam: string | null; minutes: number; days: boolean[]; categories: string[] };

/** The plan step: when the exam is (not for daily clinical review), this
 * term's subjects (term finals only), minutes a day and study days. The
 * server turns them into the study plan on the home screen. */
function PlanStep({ goal, plan, onChange }: { goal: string; plan: PlanAnswers; onChange: (p: PlanAnswers) => void }) {
  const { isFa } = useLang();
  const { data: groups } = useQuery({ queryKey: ["lesson-groups"], queryFn: lessonsApi.groups, enabled: goal === "final" });
  const categories = useMemo(() => groupByCategory(groups ?? []), [groups]);
  const section = (fa: string, en: string, body: React.ReactNode) => (
    <View style={{ gap: 10 }}>
      <AppText weight="800" size={15}>
        {isFa ? fa : en}
      </AppText>
      {body}
    </View>
  );
  return (
    <View style={{ marginTop: 22, gap: 22 }}>
      {goal !== "clinical"
        ? section("آزمونت کی است؟", "When is your exam?", (
            <ExamDatePicker value={plan.exam} onChange={(exam) => onChange({ ...plan, exam })} />
          ))
        : null}
      {goal === "final"
        ? section("درس‌های این ترم", "This term's subjects", (
            <CategoryPicker categories={categories} value={plan.categories} onChange={(categories) => onChange({ ...plan, categories })} />
          ))
        : null}
      {section("روزی چقدر وقت داری؟", "How much time a day?", (
        <MinutesPicker
          value={plan.minutes}
          options={goal === "clinical" ? CLINICAL_MINUTES : MINUTES}
          onChange={(minutes) => onChange({ ...plan, minutes })}
        />
      ))}
      {section("کدام روزها درس می‌خوانی؟", "Which days do you study?", (
        <StudyDaysPicker value={plan.days} onChange={(days) => onChange({ ...plan, days })} />
      ))}
    </View>
  );
}

function planReady(goal: string, plan: PlanAnswers) {
  if (!plan.days.some(Boolean)) return false;
  if (goal !== "clinical" && !plan.exam) return false;
  if (goal === "final" && !plan.categories.length) return false;
  return true;
}

// What the home screen puts first for each field -- shown on the last step so
// the answers visibly change something.
const START_HERE: Record<string, { icon: IconName; fa: string; en: string; descFa: string; descEn: string }[]> = {
  pharmacy: [
    {
      icon: "edu-lessons",
      fa: "درسنامه‌ی فارسی داروها",
      en: "Drug lessons in Persian",
      descFa: "دسته‌بندی‌شده بر اساس ATC",
      descEn: "Organised by ATC class",
    },
    {
      icon: "uptodate-logo",
      fa: "مرجع بالینی آپتودیت",
      en: "UpToDate clinical reference",
      descFa: "جست‌وجو در مقاله‌های مرجع",
      descEn: "Search the reference articles",
    },
    {
      icon: "lexicomp-logo",
      fa: "تداخلات دارویی",
      en: "Drug interactions",
      descFa: "بررسی چند دارو با هم، با شدت تداخل",
      descEn: "Check several drugs at once, with severity",
    },
  ],
  medicine: [
    {
      icon: "entry-diseases",
      fa: "بیماری‌ها",
      en: "Diseases",
      descFa: "مرور بیماری‌ها بر اساس تخصص",
      descEn: "Browse conditions by specialty",
    },
    {
      icon: "entry-guidelines",
      fa: "گایدلاین‌ها",
      en: "Guidelines",
      descFa: "خلاصه‌ی راهنماهای بالینی",
      descEn: "Clinical guideline summaries",
    },
    {
      icon: "entry-calculator",
      fa: "ماشین‌حساب‌های بالینی",
      en: "Clinical calculators",
      descFa: "امتیازها و فرمول‌های پرکاربرد",
      descEn: "The scores and formulas used most",
    },
  ],
};

function Check({ color, size }: { color: string; size: number }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={3}>
      <Path d="M5 12l5 5 9-10" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

export function OnboardingScreen() {
  const { isFa, lang, row, n } = useLang();
  const { colors, shadows } = useTheme();
  const setUser = useAuth((s) => s.setUser);

  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Answers>({ field: "", goal: "", level: "" });
  const [plan, setPlan] = useState<PlanAnswers>({ exam: null, minutes: 30, days: WEEKDAYS, categories: [] });
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  const isPlanStep = step === PLAN_STEP;
  const isSummary = step === SUMMARY_STEP;
  const question = QUESTIONS[step];
  const picked = question ? answers[question.key] : "";
  const clinical = answers.goal === "clinical";

  const pick = (key: keyof Answers, v: string) => {
    setAnswers({ ...answers, [key]: v });
    // A daily clinical review runs on shorter days than an exam plan.
    if (key === "goal") {
      const options = v === "clinical" ? CLINICAL_MINUTES : MINUTES;
      if (!options.includes(plan.minutes)) setPlan({ ...plan, minutes: v === "clinical" ? 10 : 30 });
    }
  };

  const label = (o: Option) => (isFa ? o.fa : o.en);
  const find = (options: Option[], v: string) => options.find((o) => o.v === v);

  const submit = async () => {
    setBusy(true);
    setFailed(false);
    try {
      setUser(
        await authApi.onboarding({
          study_field: answers.field,
          study_goal: answers.goal,
          study_level: answers.level,
          language: lang,
          exam_date: clinical ? null : plan.exam,
          daily_minutes: plan.minutes,
          study_days: plan.days,
          category_keys: answers.goal === "final" ? plan.categories : [],
        }),
      );
    } catch {
      setBusy(false);
      setFailed(true);
    }
  };

  const ctaDisabled = isSummary ? busy : isPlanStep ? !planReady(answers.goal, plan) : !picked;

  return (
    <AppShell>
      <View style={{ flex: 1, backgroundColor: colors.appBg, paddingHorizontal: 22, paddingTop: 20, paddingBottom: 28 }}>
        {/* top bar: back + three-segment progress */}
        <View style={{ flexDirection: row, alignItems: "center", gap: 12, height: 44 }}>
          {step > 0 && !isSummary ? (
            <Pressable
              onPress={() => setStep(step - 1)}
              accessibilityRole="button"
              accessibilityLabel={isFa ? "بازگشت" : "Back"}
              style={{
                width: 44,
                height: 44,
                borderRadius: 14,
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: colors.cardBg,
                borderWidth: 1,
                borderColor: colors.border,
              }}
            >
              <AppText weight="800" size={18} color={colors.ink}>
                {isFa ? "›" : "‹"}
              </AppText>
            </Pressable>
          ) : null}
          <View style={{ flex: 1, flexDirection: row, gap: 6 }}>
            {Array.from({ length: SUMMARY_STEP }, (_, i) => (
              <View
                key={i}
                style={{
                  flex: 1,
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: i <= step ? colors.accent : colors.trackBg,
                }}
              />
            ))}
          </View>
        </View>

        <ScrollView
          style={{ flex: 1 }}
          contentContainerStyle={{ paddingTop: isSummary ? 22 : 30, paddingBottom: 16 }}
          showsVerticalScrollIndicator={false}
        >
          {isPlanStep ? (
            <>
              <AppText weight="800" size={12} color={colors.accent2}>
                {isFa ? `قدم ${n(step + 1)} از ${n(SUMMARY_STEP)}` : `Step ${step + 1} of ${SUMMARY_STEP}`}
              </AppText>
              <AppText weight="900" size={26} style={{ marginTop: 6, lineHeight: 38 }}>
                {isFa ? "برنامه‌ی مطالعه‌ات" : "Your study plan"}
              </AppText>
              <AppText weight="500" size={14} muted style={{ marginTop: 6, lineHeight: 26 }}>
                {clinical
                  ? isFa
                    ? "هر روز یک مرور کوتاه برایت چیده می‌شه."
                    : "A short review is set out for you every day."
                  : isFa
                    ? "تا روز آزمون، کارهای هر روز برایت چیده می‌شه."
                    : "Each day's work is set out for you up to the exam."}
              </AppText>
              <PlanStep goal={answers.goal} plan={plan} onChange={setPlan} />
            </>
          ) : question ? (
            <>
              <AppText weight="800" size={12} color={colors.accent2}>
                {isFa
                  ? `قدم ${n(step + 1)} از ${n(SUMMARY_STEP)}`
                  : `Step ${step + 1} of ${SUMMARY_STEP}`}
              </AppText>
              <AppText weight="900" size={26} style={{ marginTop: 6, lineHeight: 38 }}>
                {question[lang].title}
              </AppText>
              <AppText weight="500" size={14} muted style={{ marginTop: 6, lineHeight: 26 }}>
                {question[lang].sub}
              </AppText>

              <View style={{ marginTop: 24, gap: 12 }}>
                {question.options.map((o, i) => {
                  const sel = picked === o.v;
                  return (
                    <Pressable
                      key={o.v}
                      onPress={() => pick(question.key, o.v)}
                      accessibilityRole="radio"
                      accessibilityState={{ checked: sel }}
                      style={[
                        {
                          flexDirection: row,
                          alignItems: "center",
                          gap: 14,
                          padding: 16,
                          borderRadius: 20,
                          backgroundColor: colors.cardBg,
                          borderWidth: 2,
                          borderColor: sel ? colors.accent : "transparent",
                        },
                        sel && shadows.raisedSm,
                      ]}
                    >
                      <View
                        style={{
                          width: 52,
                          height: 52,
                          borderRadius: 16,
                          backgroundColor: colors.softBg,
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        {o.icon ? (
                          <IconImage name={o.icon} size={34} />
                        ) : (
                          <AppText weight="900" size={18} color={colors.accent}>
                            {n(i + 1)}
                          </AppText>
                        )}
                      </View>
                      <View style={{ flex: 1, gap: 2 }}>
                        <AppText weight="800" size={16}>
                          {label(o)}
                        </AppText>
                        <AppText weight="500" size={12.5} muted>
                          {isFa ? o.descFa : o.descEn}
                        </AppText>
                      </View>
                      <View
                        style={{
                          width: 26,
                          height: 26,
                          borderRadius: 13,
                          alignItems: "center",
                          justifyContent: "center",
                          backgroundColor: sel ? colors.accent : "transparent",
                          borderWidth: sel ? 0 : 2,
                          borderColor: colors.trackBg,
                        }}
                      >
                        {sel ? <Check color={colors.onAccent} size={14} /> : null}
                      </View>
                    </Pressable>
                  );
                })}
              </View>
            </>
          ) : (
            <>
              <View style={{ alignItems: "center", gap: 10 }}>
                <View
                  style={[
                    {
                      width: 76,
                      height: 76,
                      borderRadius: 26,
                      backgroundColor: colors.accent,
                      alignItems: "center",
                      justifyContent: "center",
                    },
                    shadows.raisedSm,
                  ]}
                >
                  <Check color={colors.onAccent} size={36} />
                </View>
                <AppText weight="900" size={24} center style={{ lineHeight: 36 }}>
                  {isFa ? "مسیر یادگیری‌ات آماده‌ست" : "Your learning path is ready"}
                </AppText>
                <AppText weight="500" size={14} muted center style={{ lineHeight: 26 }}>
                  {isFa
                    ? "برنامه‌ی مطالعه‌ات در خانه، زیر «برنامهٔ مطالعه» است."
                    : "Your study plan is on the home screen, under “Study plan”."}
                </AppText>
              </View>

              {/* the plan the answers make */}
              <View
                style={[
                  { marginTop: 18, backgroundColor: colors.cardBg, borderRadius: 22, padding: 18, gap: 6 },
                  shadows.raisedSm,
                ]}
              >
                <AppText weight="800" size={12} color={colors.accent2}>
                  {isFa ? "برنامه‌ی تو" : "Your plan"}
                </AppText>
                {!clinical && plan.exam ? (
                  <AppText weight="800" size={15}>
                    {isFa
                      ? `آزمون: ${formatDay(plan.exam, true, n)}، ${n(daysUntil(plan.exam))} روز دیگر`
                      : `Exam: ${formatDay(plan.exam, false, n)}, in ${daysUntil(plan.exam)} days`}
                  </AppText>
                ) : (
                  <AppText weight="800" size={15}>
                    {isFa ? "مرور روزانه" : "Daily review"}
                  </AppText>
                )}
                <AppText weight="600" size={13} muted>
                  {isFa
                    ? `${n(plan.minutes)} دقیقه در روز، ${n(plan.days.filter(Boolean).length)} روز در هفته`
                    : `${plan.minutes} min a day, ${plan.days.filter(Boolean).length} days a week`}
                </AppText>
              </View>

              <View
                style={{
                  marginTop: 18,
                  flexDirection: row,
                  flexWrap: "wrap",
                  justifyContent: "center",
                  alignItems: "center",
                  gap: 8,
                }}
              >
                {[find(FIELDS, answers.field), find(GOALS, answers.goal), find(LEVELS, answers.level)].map((o) =>
                  o ? (
                    <View
                      key={o.v}
                      style={{
                        paddingHorizontal: 13,
                        paddingVertical: 6,
                        borderRadius: 999,
                        backgroundColor: colors.cardBg,
                        borderWidth: 1,
                        borderColor: colors.trackBg,
                      }}
                    >
                      <AppText weight="700" size={12.5} color={colors.accent}>
                        {label(o)}
                      </AppText>
                    </View>
                  ) : null,
                )}
                <Pressable onPress={() => setStep(0)} accessibilityRole="button" hitSlop={8} style={{ padding: 6 }}>
                  <AppText weight="800" size={12.5} color={colors.accent}>
                    {isFa ? "ویرایش" : "Edit"}
                  </AppText>
                </Pressable>
              </View>

              <View
                style={[
                  { marginTop: 20, backgroundColor: colors.cardBg, borderRadius: 22, padding: 18 },
                  shadows.raisedSm,
                ]}
              >
                <AppText weight="800" size={12} color={colors.accent2} style={{ marginBottom: 6 }}>
                  {isFa ? "از اینجا شروع کن" : "Start here"}
                </AppText>
                {(START_HERE[answers.field] ?? START_HERE.pharmacy).map((item, i, all) => (
                  <View
                    key={item.icon}
                    style={{
                      flexDirection: row,
                      alignItems: "center",
                      gap: 12,
                      paddingVertical: 10,
                      borderBottomWidth: i < all.length - 1 ? 1 : 0,
                      borderBottomColor: colors.sheetLine,
                    }}
                  >
                    <View
                      style={{
                        width: 42,
                        height: 42,
                        borderRadius: 13,
                        backgroundColor: colors.softBg,
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <IconImage name={item.icon} size={28} />
                    </View>
                    <View style={{ flex: 1, gap: 1 }}>
                      <AppText weight="800" size={14.5}>
                        {isFa ? item.fa : item.en}
                      </AppText>
                      <AppText weight="500" size={12} muted>
                        {isFa ? item.descFa : item.descEn}
                      </AppText>
                    </View>
                  </View>
                ))}
              </View>
            </>
          )}
        </ScrollView>

        {failed ? (
          <AppText weight="700" size={13} color={colors.denyLabel} center style={{ marginBottom: 10 }}>
            {isFa ? "ذخیره نشد. دوباره تلاش کن." : "Couldn't save. Please try again."}
          </AppText>
        ) : null}

        <Pressable
          onPress={() => (isSummary ? submit() : setStep(step + 1))}
          disabled={ctaDisabled}
          accessibilityRole="button"
          style={[
            {
              height: 56,
              borderRadius: 18,
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: colors.accent,
              opacity: ctaDisabled ? 0.5 : 1,
            },
            !ctaDisabled && shadows.raisedSm,
          ]}
        >
          <AppText weight="800" size={16} color={colors.onAccent}>
            {isSummary ? (isFa ? "ورود به خانه" : "Go to home") : isFa ? "ادامه" : "Continue"}
          </AppText>
        </Pressable>
      </View>
    </AppShell>
  );
}
