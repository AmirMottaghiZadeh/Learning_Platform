import { useMutation, useQuery } from "@tanstack/react-query";
import React, { useEffect, useRef, useState } from "react";
import { Pressable, View } from "react-native";
import Svg, { Circle } from "react-native-svg";

import { ApiError } from "@/api/client";
import { lessonsApi, quizApi } from "@/api/endpoints";
import { QuizAnswerResult, QuizResult, QuizSession, SectionTone } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { IconImage } from "@/components/primitives/IconImage";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useBackInterceptor } from "@/navigation/back";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";
import { toneColors } from "@/theme/tone";
import { QuizSetup } from "@/components/quiz/QuizSetup";

/** "metronidazole-10432" -> "metronidazole" -- the ingredient slug is a
 * name plus its RxNorm RXCUI (apps.drugs.models.Ingredient.build_slug), and
 * only the name is worth showing as context on a question card. */
function drugNameFromSlug(slug: string): string {
  return slug.replace(/-\d+$/, "").replace(/-/g, " ");
}

/** A chip needs a visible fill/border even for the "info" tone, which
 * toneColors() leaves transparent (it's meant for a full section block,
 * not a small chip) -- everything else it returns is used as-is. */
function chipColors(tone: SectionTone, colors: ReturnType<typeof useTheme>["colors"]) {
  if (tone === "info") return { bg: colors.accent + "14", border: colors.accent, label: colors.accent };
  return toneColors(tone, colors);
}

export function QuizScreen() {
  const { t, isFa, n, row } = useLang();
  const { colors } = useTheme();
  const setTab = useNav((s) => s.setTab);
  const goBack = useNav((s) => s.goBack);
  // Set when this screen was opened from the end of a drug's lesson page
  // ("test yourself on this drug") rather than from the quiz browser -- skips
  // the topic-picker setup stage entirely and auto-starts a session scoped
  // to just this one ingredient's bank questions.
  const ingredientSlug = String(useNav((s) => s.params.ingredientSlug ?? ""));
  const autoStarted = useRef(false);

  const [lastSelection, setLastSelection] = useState<{ category: string; atc_code: string; count: number }>();
  const [stage, setStage] = useState<"setup" | "running" | "done">("setup");
  const [locked, setLocked] = useState(false);
  const [insufficientData, setInsufficientData] = useState(false);

  const { data: groups } = useQuery({ queryKey: ["lesson-groups"], queryFn: lessonsApi.groups });
  const [session, setSession] = useState<QuizSession | null>(null);
  const [index, setIndex] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [answerResult, setAnswerResult] = useState<QuizAnswerResult | null>(null);
  const [runningScore, setRunningScore] = useState({ correct: 0, total: 0 });
  const [result, setResult] = useState<QuizResult | null>(null);

  const resetRun = () => {
    setIndex(0);
    setPicked(null);
    setAnswerResult(null);
    setRunningScore({ correct: 0, total: 0 });
  };

  const start = useMutation({
    mutationFn: (selection?: { category: string; atc_code: string; count: number }) =>
      ingredientSlug
        ? quizApi.start({ ingredient_slug: ingredientSlug })
        : quizApi.start(selection!),
    onSuccess: (s) => {
      setSession(s);
      resetRun();
      setStage("running");
    },
    onError: (e) => {
      if (e instanceof ApiError && e.status === 503) setLocked(true);
      else if (e instanceof ApiError && e.status === 422) setInsufficientData(true);
      // Anything else (400/500/network): surfaced generically below rather
      // than silently doing nothing, which is indistinguishable from the
      // button not being wired up at all.
    },
  });

  useEffect(() => {
    if (ingredientSlug && !autoStarted.current) {
      autoStarted.current = true;
      start.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ingredientSlug]);

  const answer = useMutation({
    mutationFn: (selected: number) =>
      quizApi.answer(session!.id, {
        question_id: session!.questions[index].id,
        selected_index: selected,
        client_answered_at: new Date().toISOString(),
      }),
    onSuccess: (r) => {
      setAnswerResult(r);
      setRunningScore((s) => ({ correct: s.correct + (r.correct ? 1 : 0), total: s.total + 1 }));
    },
  });

  const quizErrorMessage = (error: unknown, fallback: string) => {
    if (!(error instanceof ApiError)) return fallback;
    if (error.code === "QUOTA_EXCEEDED") return t("quizQuotaExceeded");
    if (error.code === "PREMIUM_REQUIRED") return t("quizPremiumRequired");
    if (error.status === 401) return t("quizLoginRequired");
    return error.message;
  };

  const finish = useMutation({
    mutationFn: () => quizApi.finish(session!.id),
    onSuccess: (r) => {
      setResult(r);
      setStage("done");
    },
  });

  const reviewMistakes = useMutation({
    mutationFn: () => quizApi.reviewMistakes(session!.id),
    onSuccess: (s) => {
      setSession(s);
      resetRun();
      setResult(null);
      setStage("running");
    },
  });

  const exitToSetup = () => {
    setSession(null);
    setResult(null);
    setStage("setup");
  };
  // A drug self-test has no setup to return to -- its "back" is the real
  // nav history, back to the lesson page it was opened from.
  const backFromRun = ingredientSlug ? goBack : exitToSetup;
  useBackInterceptor(stage !== "setup" && !ingredientSlug, exitToSetup);
  const goHome = () => setTab("dashboard");

  if (locked) {
    return (
      <Screen>
        <ScreenChrome title={t("quizSetupTitle")} tour="quiz" />
        <Card>
          <View style={{ alignItems: "center", gap: 12, paddingVertical: 24 }}>
            <View
              style={{
                width: 60,
                height: 60,
                borderRadius: 18,
                backgroundColor: colors.softBg,
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <IconImage name="edu-quiz" size={34} />
            </View>
            <AppText weight="800" size={15}>
              {t("comingSoon")}
            </AppText>
            <AppText muted weight="600" size={13} center>
              {t("lockedFeature")}
            </AppText>
          </View>
        </Card>
      </Screen>
    );
  }

  if (ingredientSlug && stage === "setup") {
    return (
      <Screen>
        <ScreenChrome title={drugNameFromSlug(ingredientSlug)} onBack={goBack} help="quiz" />
        <Card>
          <View style={{ alignItems: "center", gap: 12, paddingVertical: 24 }}>
            <View
              style={{
                width: 60,
                height: 60,
                borderRadius: 18,
                backgroundColor: colors.softBg,
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <IconImage name="edu-quiz" size={34} />
            </View>
            {insufficientData ? (
              <AppText weight="700" size={13} color={colors.denyLabel} center>
                {t("quizInsufficientData")}
              </AppText>
            ) : start.isError ? (
              <AppText weight="700" size={13} color={colors.denyLabel} center>
                {quizErrorMessage(start.error, t("quizStartFailed"))}
              </AppText>
            ) : (
              <AppText muted weight="600" size={13} center>
                {t("quizStartBtn")}…
              </AppText>
            )}
          </View>
        </Card>
      </Screen>
    );
  }

  if (stage === "setup") {
    return <QuizSetup pending={start.isPending} initialSelection={lastSelection}
      onSelectionChange={() => { start.reset(); setInsufficientData(false); }}
      error={insufficientData ? t("quizInsufficientData") : start.isError ? quizErrorMessage(start.error, t("quizStartFailed")) : undefined}
      onStart={(category, atc_code, count) => { setInsufficientData(false); setLastSelection({ category, atc_code, count }); start.mutate({ category, atc_code, count }); }} />;
  }

  if (stage === "done" && result) {
    const pct = result.total ? Math.round((100 * result.score) / result.total) : 0;
    const r = 50;
    const circumference = 2 * Math.PI * r;
    const offset = circumference * (1 - pct / 100);
    const diff = result.previous_best_pct !== null ? pct - result.previous_best_pct : null;

    return (
      <Screen>
        <ScreenChrome title={t("quizResultTitle")} onBack={backFromRun} help="quiz" />

        <View style={{ alignItems: "center", marginBottom: 14 }}>
          <View style={{ width: 116, height: 116, marginBottom: 10 }}>
            <Svg width={116} height={116} viewBox="0 0 116 116" style={{ position: "absolute", transform: [{ rotate: "-90deg" }] }}>
              <Circle cx={58} cy={58} r={r} fill="none" stroke={colors.trackBg} strokeWidth={10} />
              <Circle
                cx={58} cy={58} r={r} fill="none" stroke={colors.accent} strokeWidth={10}
                strokeLinecap="round" strokeDasharray={`${circumference} ${circumference}`} strokeDashoffset={offset}
              />
            </Svg>
            <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
              <AppText weight="900" size={26}>{n(pct)}٪</AppText>
              <AppText muted weight="700" size={10.5}>{n(result.score)}/{n(result.total)}</AppText>
            </View>
          </View>
          {diff !== null ? (
            <View style={{ flexDirection: row, alignItems: "center", gap: 6, paddingHorizontal: 12, paddingVertical: 5, borderRadius: 999, backgroundColor: diff >= 0 ? colors.accent + "1a" : colors.denyBg }}>
              <AppText weight="800" size={11} color={diff >= 0 ? colors.accent : colors.denyLabel}>
                {diff >= 0 ? "↑" : "↓"} {n(Math.abs(diff))}٪ {diff >= 0 ? t("quizBetterThanBest") : t("quizWorseThanBest")} ({n(result.previous_best_pct!)}٪)
              </AppText>
            </View>
          ) : (
            <AppText muted weight="600" size={11}>{t("quizPreviousBest")}: —</AppText>
          )}
        </View>

        {result.by_field.length > 0 ? (
          <>
            <AppText weight="800" size={12} style={{ marginBottom: 8 }}>{t("quizPerformanceByType")}</AppText>
            <View style={{ gap: 7, marginBottom: 18 }}>
              {result.by_field.map((f) => {
                const cc = chipColors(f.tone, colors);
                const pctF = f.total ? (100 * f.correct) / f.total : 0;
                return (
                  <View key={f.field} style={{ flexDirection: row, alignItems: "center", gap: 8 }}>
                    <AppText weight="700" size={10.5} muted style={{ width: 68 }}>{f.label_fa}</AppText>
                    <View style={{ flex: 1, height: 7, borderRadius: 999, backgroundColor: colors.trackBg, overflow: "hidden" }}>
                      <View style={{ width: `${pctF}%`, height: 7, backgroundColor: cc.label }} />
                    </View>
                    <AppText weight="800" size={10.5} style={{ width: 30, textAlign: "left" }}>{n(f.correct)}/{n(f.total)}</AppText>
                  </View>
                );
              })}
            </View>
          </>
        ) : null}

        {result.missed.length > 0 ? (
          <>
            <AppText weight="800" size={12} style={{ marginBottom: 8 }}>{t("quizYourMistakes")}</AppText>
            <View style={{ gap: 8, marginBottom: 18 }}>
              {result.missed.map((m, i) => (
                <Card key={i} soft style={{ gap: 6 }}>
                  <AppText weight="700" size={12} style={{ lineHeight: 18 }}>
                    {m.prompt_fa}
                  </AppText>
                  <View style={{ flexDirection: row, alignItems: "center", gap: 5 }}>
                    <AppText size={10} color={colors.accent}>✓</AppText>
                    <AppText weight="700" size={10.5} color={colors.accent} style={{ flex: 1 }}>
                      {m.options_fa[m.correct_index]}
                    </AppText>
                  </View>
                </Card>
              ))}
            </View>
          </>
        ) : null}

        <View style={{ gap: 9 }}>
          {result.missed.length > 0 ? (
            <Button
              label={`${t("quizReviewMistakesBtn")} ${n(result.missed.length)} ${t("quizMistakeCountSuffix")}`}
              onPress={() => reviewMistakes.mutate()}
              loading={reviewMistakes.isPending}
            />
          ) : null}
          <Button label={t("quizBackHome")} variant="secondary" onPress={goHome} />
        </View>
      </Screen>
    );
  }

  // running
  const selectedTopic = groups?.find((group) => group.code === session!.category);
  const q = session!.questions[index];
  const options = isFa ? q.options_fa : q.options_en;
  const answered = answerResult !== null;
  const correctIndex = answerResult?.correct_index ?? null;
  const progress = ((index + (answered ? 1 : 0)) / session!.questions.length) * 100;
  const fieldTag = chipColors(q.field_tone, colors);
  const drugName = drugNameFromSlug(q.subject_slug);
  const scoreGood = runningScore.total === 0 || runningScore.correct / runningScore.total >= 0.5;

  return (
    <Screen>
      <ScreenChrome title={t("quizTitle")} onBack={backFromRun} help="quiz" />

      <View style={{ flexDirection: row, alignItems: "center", gap: 8, marginBottom: 10 }}>
        <AppText weight="800" size={11.5} muted style={{ flex: 1 }}>
          {isFa ? selectedTopic?.name_fa ?? session!.category : selectedTopic?.name_en ?? session!.category}
        </AppText>
        <View style={{ flexDirection: row, alignItems: "center", gap: 5, backgroundColor: colors.softBg, borderWidth: 1, borderColor: colors.trackBg, borderRadius: 999, paddingHorizontal: 9, paddingVertical: 4 }}>
          <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: scoreGood ? colors.accent : colors.denyLabel }} />
          <AppText weight="800" size={10.5}>
            {n(runningScore.correct)}/{n(runningScore.total)} {t("quizRunningScore")}
          </AppText>
        </View>
      </View>

      <View style={{ flexDirection: row, alignItems: "center", gap: 8, marginBottom: spacing.lg }}>
        <View style={{ flex: 1, height: 6, borderRadius: 999, backgroundColor: colors.trackBg, overflow: "hidden" }}>
          <View style={{ width: `${progress}%`, height: 6, backgroundColor: colors.accent }} />
        </View>
        <AppText weight="800" size={12} muted>
          {n(index + 1)}/{n(session!.questions.length)}
        </AppText>
      </View>

      <Card>
        <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
          <View style={{ paddingHorizontal: 9, paddingVertical: 4, borderRadius: 999, backgroundColor: fieldTag.bg, borderWidth: 1, borderColor: fieldTag.border }}>
            <AppText weight="800" size={10} color={fieldTag.label}>{q.field_label_fa}</AppText>
          </View>
          <AppText weight="800" size={10.5} muted style={{ textAlign: "left", writingDirection: "ltr" }}>{drugName}</AppText>
        </View>
        <AppText weight="800" size={15} style={{ lineHeight: 25 }}>
          {isFa ? q.prompt_fa : q.prompt_en}
        </AppText>
      </Card>

      <View style={{ gap: 10, marginTop: 16 }}>
        {options.map((label, i) => {
          let bg = colors.optBg;
          let border = colors.trackBg;
          let tag: string | null = null;
          let tagColor = colors.accent;
          if (answered && i === correctIndex) {
            bg = colors.accent + "1a";
            border = colors.accent;
            tag = t("quizCorrectAnswer");
            tagColor = colors.accent;
          } else if (answered && i === picked && i !== correctIndex) {
            bg = colors.denyBg;
            border = colors.denyBorder;
            tag = t("quizYourAnswer");
            tagColor = colors.denyLabel;
          }
          const dim = answered && i !== correctIndex && i !== picked;
          return (
            <Pressable
              key={i}
              disabled={answered || answer.isPending}
              onPress={() => {
                setPicked(i);
                answer.mutate(i);
              }}
              style={{ padding: 14, borderRadius: 14, backgroundColor: bg, borderWidth: 1.5, borderColor: border, opacity: dim ? 0.5 : 1 }}
            >
              <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between", gap: 8 }}>
                <AppText weight="600" size={13.5} style={{ flex: 1 }}>
                  {label}
                </AppText>
                {answered && i === correctIndex ? <AppText color={colors.accent}>✓</AppText> : null}
                {answered && i === picked && i !== correctIndex ? <AppText color={colors.denyLabel}>×</AppText> : null}
              </View>
              {tag ? (
                <AppText weight="700" size={9.5} color={tagColor} style={{ marginTop: 4 }}>
                  {tag}
                </AppText>
              ) : null}
            </Pressable>
          );
        })}
      </View>

      {answer.isError ? (
        <AppText color={colors.denyLabel} style={{ marginTop: spacing.md }}>
          {quizErrorMessage(answer.error, t("quizAnswerFailed"))}
        </AppText>
      ) : null}

      {answered && answerResult.extra_context.length > 0 ? (
        <View style={{ backgroundColor: colors.softBg, borderRadius: 16, padding: 14, marginTop: 16 }}>
          <View style={{ flexDirection: row, alignItems: "center", gap: 7, marginBottom: 8 }}>
            <View style={{ width: 18, height: 18, borderRadius: 9, backgroundColor: colors.accent, alignItems: "center", justifyContent: "center" }}>
              <AppText weight="900" size={10} color={colors.onAccent}>i</AppText>
            </View>
            <AppText weight="800" size={11.5}>
              {t("quizExplainMoreAbout")} {drugName}
            </AppText>
          </View>
          <View style={{ gap: 6 }}>
            {answerResult.extra_context.map((text, i) => (
              <View key={i} style={{ flexDirection: row, gap: 7, alignItems: "flex-start" }}>
                <View style={{ width: 4, height: 4, borderRadius: 2, backgroundColor: colors.muted, marginTop: 7 }} />
                <AppText weight="600" size={11} muted style={{ flex: 1, lineHeight: 17 }}>
                  {text}
                </AppText>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {answered ? (
        <Button
          label={index + 1 < session!.questions.length ? t("quizNext") : t("quizResultTitle")}
          onPress={() => {
            if (index + 1 < session!.questions.length) {
              setIndex(index + 1);
              setPicked(null);
              setAnswerResult(null);
              answer.reset();
            } else {
              finish.mutate();
            }
          }}
          loading={finish.isPending}
          style={{ marginTop: spacing.lg }}
        />
      ) : (
        <View style={{ height: 52, borderRadius: 16, backgroundColor: colors.softBg, borderWidth: 1.5, borderColor: colors.trackBg, alignItems: "center", justifyContent: "center", marginTop: spacing.lg }}>
          <AppText weight="700" size={13.5} muted>{t("quizSelectAnOption")}</AppText>
        </View>
      )}
    </Screen>
  );
}
