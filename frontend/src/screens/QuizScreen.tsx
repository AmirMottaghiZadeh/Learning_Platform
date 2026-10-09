import { useMutation, useQuery } from "@tanstack/react-query";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Pressable, ScrollView, TextInput, View } from "react-native";
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
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { layout, spacing } from "@/theme/tokens";
import { toneColors } from "@/theme/tone";
import { groupByCategory } from "@/utils/lessonCategories";

const COUNTS = [5, 10, 15, 20];
const MASTERY_HIGH = 70;
const MASTERY_MID = 40;

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

function masteryColors(pct: number, colors: ReturnType<typeof useTheme>["colors"]) {
  if (pct >= MASTERY_HIGH) return { bg: colors.accent + "1a", label: colors.accent };
  if (pct >= MASTERY_MID) return { bg: colors.cautBg, label: colors.cautLabel };
  return { bg: colors.denyBg, label: colors.denyLabel };
}

export function QuizScreen() {
  const { t, isFa, n, row } = useLang();
  const { colors } = useTheme();
  const setTab = useNav((s) => s.setTab);
  const goBack = useNav((s) => s.goBack);
  // Set when this screen was opened from the end of a drug's lesson page
  // ("test yourself on this drug") rather than from the quiz tab -- skips
  // the topic-picker setup stage entirely and auto-starts a session scoped
  // to just this one ingredient's bank questions.
  const ingredientSlug = String(useNav((s) => s.params.ingredientSlug ?? ""));
  const autoStarted = useRef(false);

  const [stage, setStage] = useState<"setup" | "running" | "done">("setup");
  // `topicKey` is a clinical study-topic code (same taxonomy Lessons browses
  // by, so picking a subject here means the same thing there); `atcCode`
  // optionally narrows it to one ATC chapter within that topic.
  const [topicKey, setTopicKey] = useState<string | null>(null);
  const [atcCode, setAtcCode] = useState("");
  const [countIdx, setCountIdx] = useState(1); // COUNTS[1] = 10
  const count = COUNTS[countIdx];
  const [search, setSearch] = useState("");
  const [locked, setLocked] = useState(false);
  const [insufficientData, setInsufficientData] = useState(false);

  const [session, setSession] = useState<QuizSession | null>(null);
  const [index, setIndex] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [answerResult, setAnswerResult] = useState<QuizAnswerResult | null>(null);
  const [runningScore, setRunningScore] = useState({ correct: 0, total: 0 });
  const [result, setResult] = useState<QuizResult | null>(null);

  const { data: groups, isLoading: groupsLoading } = useQuery({
    queryKey: ["lesson-groups"],
    queryFn: lessonsApi.groups,
  });
  const categories = useMemo(() => groupByCategory(groups ?? []), [groups]);
  const selectedTopic = groups?.find((g) => g.code === topicKey) ?? null;

  const { data: overview } = useQuery({ queryKey: ["quiz-overview"], queryFn: quizApi.overview });
  const { data: preview } = useQuery({
    queryKey: ["quiz-preview", topicKey, atcCode, count],
    queryFn: () => quizApi.preview(topicKey ?? "", atcCode, count),
    enabled: !!topicKey,
  });

  const filteredCategories = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return categories;
    return categories
      .map((c) => ({ ...c, topics: c.topics.filter((top) => (isFa ? top.name_fa : top.name_en).toLowerCase().includes(q)) }))
      .filter((c) => c.topics.length > 0);
  }, [categories, search, isFa]);

  const pickTopic = (code: string) => {
    setTopicKey((cur) => (cur === code ? null : code));
    setAtcCode("");
    setInsufficientData(false);
  };

  const resetRun = () => {
    setIndex(0);
    setPicked(null);
    setAnswerResult(null);
    setRunningScore({ correct: 0, total: 0 });
  };

  const start = useMutation({
    mutationFn: () =>
      ingredientSlug
        ? quizApi.start({ ingredient_slug: ingredientSlug })
        : quizApi.start({ category: topicKey!, atc_code: atcCode, count }),
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
  const goHome = () => setTab("dashboard");

  if (locked) {
    return (
      <Screen>
        <ScreenChrome title={t("quizSetupTitle")} help="quiz" />
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
                {start.error instanceof ApiError ? start.error.message : t("quizStartFailed")}
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
    const willHaveEnough = !preview || preview.available >= count;
    return (
      <Screen scroll={false} padded={false}>
        <View style={{ flex: 1, padding: layout.screenPadding, paddingBottom: 0 }}>
          <ScreenChrome title={t("quizSetupTitle")} help="quiz" />

          {overview ? (
            <View style={{ flexDirection: row, gap: 8, marginBottom: 12 }}>
              <StatTile value={`${n(overview.avg_score_pct)}٪`} label={t("quizStatAvgScore")} color={colors.accent} />
              <StatTile value={n(overview.total_quizzes)} label={t("quizStatTotalQuizzes")} />
              <StatTile value={n(overview.weak_topics_count)} label={t("quizStatWeakTopics")} color={colors.cautLabel} />
            </View>
          ) : null}

          <View
            style={{
              flexDirection: row,
              alignItems: "center",
              gap: 8,
              backgroundColor: colors.inputBg,
              borderWidth: 1,
              borderColor: colors.trackBg,
              borderRadius: 13,
              paddingHorizontal: 13,
              paddingVertical: 10,
              marginBottom: 12,
            }}
          >
            <AppText muted size={12}>⌕</AppText>
            <TextInput
              value={search}
              onChangeText={setSearch}
              placeholder={t("quizSearchTopicPlaceholder")}
              placeholderTextColor={colors.muted}
              style={{
                flex: 1,
                fontFamily: fontFamily("600"),
                fontSize: 12.5,
                color: colors.ink,
                textAlign: isFa ? "right" : "left",
                writingDirection: isFa ? "rtl" : "ltr",
                padding: 0,
              }}
            />
          </View>

          <AppText weight="800" size={11.5} muted style={{ marginBottom: 8 }}>
            {t("quizCategoryLabel")}
          </AppText>

          {groupsLoading ? (
            <LoadingState />
          ) : (
            <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 12 }}>
              <View style={{ gap: 14 }}>
                {filteredCategories.map((category) => (
                  <View key={category.code}>
                    <AppText weight="800" size={11} muted style={{ marginBottom: 6 }}>
                      {isFa ? category.name_fa : category.name_en}
                    </AppText>
                    <View style={{ gap: 8 }}>
                      {category.topics.map((topic) => {
                        const sel = topicKey === topic.code;
                        const totalDrugs = topic.subgroups.reduce((a, s) => a + s.total, 0);
                        const mastery = overview?.mastery[topic.code];

                        if (!sel) {
                          const mc = mastery !== undefined ? masteryColors(mastery, colors) : null;
                          return (
                            <Pressable
                              key={topic.code}
                              onPress={() => pickTopic(topic.code)}
                              style={{
                                flexDirection: row,
                                alignItems: "center",
                                gap: 10,
                                paddingVertical: 9,
                                paddingHorizontal: 12,
                                borderRadius: 12,
                                backgroundColor: colors.cardBg,
                                borderWidth: 1,
                                borderColor: colors.trackBg,
                              }}
                            >
                              <AppText weight="700" size={12.5} style={{ flex: 1 }}>
                                {isFa ? topic.name_fa : topic.name_en}
                              </AppText>
                              <View
                                style={{
                                  paddingHorizontal: 8,
                                  paddingVertical: 3,
                                  borderRadius: 999,
                                  backgroundColor: mc ? mc.bg : colors.softBg,
                                }}
                              >
                                <AppText weight="800" size={9.5} color={mc ? mc.label : colors.muted}>
                                  {mastery !== undefined ? `${n(mastery)}٪` : t("quizNewTopic")}
                                </AppText>
                              </View>
                            </Pressable>
                          );
                        }

                        return (
                          <View
                            key={topic.code}
                            style={{
                              backgroundColor: colors.cardBg,
                              borderWidth: 2,
                              borderColor: colors.accent,
                              borderRadius: 16,
                              padding: 14,
                            }}
                          >
                            <View style={{ flexDirection: row, alignItems: "center", gap: 10, marginBottom: 12 }}>
                              <View
                                style={{
                                  width: 34, height: 34, borderRadius: 11,
                                  backgroundColor: colors.accent, alignItems: "center", justifyContent: "center",
                                }}
                              >
                                <AppText weight="900" size={12} color={colors.onAccent}>
                                  {(isFa ? topic.name_fa : topic.name_en).slice(0, 2)}
                                </AppText>
                              </View>
                              <View style={{ flex: 1 }}>
                                <AppText weight="800" size={13.5}>
                                  {isFa ? topic.name_fa : topic.name_en}
                                </AppText>
                                <AppText muted weight="700" size={10.5} style={{ marginTop: 1 }}>
                                  {n(totalDrugs)} {t("quizDrugCount")}
                                </AppText>
                              </View>
                              {mastery !== undefined ? (
                                <View style={{ paddingHorizontal: 9, paddingVertical: 5, borderRadius: 999, backgroundColor: colors.accent + "1a" }}>
                                  <AppText weight="800" size={10.5} color={colors.accent}>
                                    {t("quizMastery")} {n(mastery)}٪
                                  </AppText>
                                </View>
                              ) : null}
                            </View>

                            <View style={{ flexDirection: row, flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
                              <Chip
                                label={t("quizAllChapters")}
                                active={atcCode === ""}
                                onPress={() => setAtcCode("")}
                                activeColors={{ bg: colors.accent, border: colors.accent, label: colors.onAccent }}
                              />
                              {topic.subgroups.map((sub) => (
                                <Chip
                                  key={sub.code}
                                  label={`${sub.code} ${isFa ? sub.name_fa : sub.name_en}`}
                                  active={atcCode === sub.code}
                                  onPress={() => setAtcCode(sub.code)}
                                  activeColors={{ bg: colors.accent, border: colors.accent, label: colors.onAccent }}
                                />
                              ))}
                            </View>

                            {preview && preview.by_field.length > 0 ? (
                              <>
                                <AppText muted weight="800" size={9.5} style={{ marginBottom: 7 }}>
                                  {t("quizThisQuizCovers")}
                                </AppText>
                                <View style={{ flexDirection: row, flexWrap: "wrap", gap: 6, marginBottom: 13 }}>
                                  {preview.by_field.map((f) => {
                                    const cc = chipColors(f.tone, colors);
                                    return (
                                      <View
                                        key={f.field}
                                        style={{
                                          paddingVertical: 6, paddingHorizontal: 10, borderRadius: 10,
                                          backgroundColor: cc.bg, borderWidth: 1, borderColor: cc.border,
                                        }}
                                      >
                                        <AppText weight="700" size={10} color={cc.label}>
                                          {f.label_fa} {n(f.count)}
                                        </AppText>
                                      </View>
                                    );
                                  })}
                                </View>
                              </>
                            ) : null}

                            <View
                              style={{
                                flexDirection: row, alignItems: "center", justifyContent: "space-between",
                                paddingTop: 11, borderTopWidth: 1, borderTopColor: colors.softBg,
                              }}
                            >
                              <View>
                                <AppText weight="700" size={10} muted>{t("quizCountLabel")}</AppText>
                                {preview ? (
                                  <AppText weight="600" size={9.5} color={colors.muted} style={{ marginTop: 1 }}>
                                    ~{n(preview.estimated_minutes)} {t("quizEstimatedMinutes")}
                                  </AppText>
                                ) : null}
                              </View>
                              <View style={{ flexDirection: row, alignItems: "center", gap: 12 }}>
                                <Pressable
                                  onPress={() => setCountIdx((i) => Math.max(0, i - 1))}
                                  style={{ width: 26, height: 26, borderRadius: 13, backgroundColor: colors.softBg, borderWidth: 1, borderColor: colors.trackBg, alignItems: "center", justifyContent: "center" }}
                                >
                                  <AppText weight="800" size={13}>−</AppText>
                                </Pressable>
                                <AppText weight="900" size={14} style={{ minWidth: 18, textAlign: "center" }}>{n(count)}</AppText>
                                <Pressable
                                  onPress={() => setCountIdx((i) => Math.min(COUNTS.length - 1, i + 1))}
                                  style={{ width: 26, height: 26, borderRadius: 13, backgroundColor: colors.accent, alignItems: "center", justifyContent: "center" }}
                                >
                                  <AppText weight="800" size={13} color={colors.onAccent}>+</AppText>
                                </Pressable>
                              </View>
                            </View>
                            {!willHaveEnough ? (
                              <AppText size={10.5} weight="700" color={colors.denyLabel} style={{ marginTop: 8 }}>
                                {t("quizInsufficientData")}
                              </AppText>
                            ) : null}
                          </View>
                        );
                      })}
                    </View>
                  </View>
                ))}
              </View>
            </ScrollView>
          )}
        </View>

        <View
          style={{
            padding: 14,
            // BottomNav overlays the screen (position: absolute) instead of
            // taking flex space -- Screen's own scroll={true} path reserves
            // room for it via contentContainerStyle, but scroll={false}
            // (used here for the sticky footer) doesn't, so this footer has
            // to reserve it itself or it renders half-hidden behind the nav.
            paddingBottom: layout.bottomNavHeight + 14,
            backgroundColor: colors.appBg,
            borderTopWidth: 1,
            borderTopColor: colors.trackBg,
          }}
        >
          {insufficientData ? (
            <AppText size={11.5} weight="700" color={colors.denyLabel} style={{ marginBottom: 10, textAlign: "center" }}>
              {t("quizInsufficientData")}
            </AppText>
          ) : null}
          {start.isError && !insufficientData && !locked ? (
            <AppText size={11.5} weight="700" color={colors.denyLabel} style={{ marginBottom: 10, textAlign: "center" }}>
              {start.error instanceof ApiError ? start.error.message : t("quizStartFailed")}
            </AppText>
          ) : null}
          <Button
            label={topicKey ? `${t("quizStartBtn")} · ${n(count)}` : t("quizStartBtn")}
            onPress={() => start.mutate()}
            loading={start.isPending}
            disabled={!topicKey || !willHaveEnough}
          />
          {!topicKey ? (
            <AppText muted size={11} weight="600" center style={{ marginTop: 8 }}>
              {t("quizNoTopicSelected")}
            </AppText>
          ) : null}
        </View>
      </Screen>
    );
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
              disabled={answered}
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

function StatTile({ value, label, color }: { value: string; label: string; color?: string }) {
  const { colors } = useTheme();
  return (
    <View style={{ flex: 1, backgroundColor: colors.cardBg, borderWidth: 1, borderColor: colors.trackBg, borderRadius: 13, padding: 10 }}>
      <AppText weight="900" size={16} color={color}>{value}</AppText>
      <AppText muted weight="700" size={9.5} style={{ marginTop: 2 }}>{label}</AppText>
    </View>
  );
}

function Chip({
  label,
  active,
  onPress,
  activeColors,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
  activeColors: { bg: string; border: string; label: string };
}) {
  const { colors } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={{
        paddingVertical: 6,
        paddingHorizontal: 10,
        borderRadius: 10,
        backgroundColor: active ? activeColors.bg : colors.softBg,
        borderWidth: 1,
        borderColor: active ? activeColors.border : colors.trackBg,
      }}
    >
      <AppText weight="700" size={10.5} color={active ? activeColors.label : colors.ink}>
        {label}
      </AppText>
    </Pressable>
  );
}
