import { useMutation } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { ApiError } from "@/api/client";
import { quizApi } from "@/api/endpoints";
import { QuizResult, QuizSession } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { IconImage } from "@/components/primitives/IconImage";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

const CATEGORIES = [
  { key: "general", fa: "داروشناسی عمومی", en: "General pharmacology" },
  { key: "antibiotics", fa: "آنتی‌بیوتیک‌ها", en: "Antibiotics" },
  { key: "cardio", fa: "قلب و عروق", en: "Cardiovascular" },
  { key: "interactions", fa: "تداخلات دارویی", en: "Drug interactions" },
];
const COUNTS = [5, 10, 15, 20];

export function QuizScreen() {
  const { t, isFa, n, row } = useLang();
  const { colors } = useTheme();

  const [stage, setStage] = useState<"setup" | "running" | "done">("setup");
  const [category, setCategory] = useState("general");
  const [count, setCount] = useState(10);
  const [locked, setLocked] = useState(false);

  const [session, setSession] = useState<QuizSession | null>(null);
  const [index, setIndex] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [correctIndex, setCorrectIndex] = useState<number | null>(null);
  const [result, setResult] = useState<QuizResult | null>(null);

  const start = useMutation({
    mutationFn: () => quizApi.start({ category, count }),
    onSuccess: (s) => {
      setSession(s);
      setIndex(0);
      setPicked(null);
      setCorrectIndex(null);
      setStage("running");
    },
    onError: (e) => {
      if (e instanceof ApiError && e.status === 503) setLocked(true);
    },
  });

  const answer = useMutation({
    mutationFn: (selected: number) =>
      quizApi.answer(session!.id, {
        question_id: session!.questions[index].id,
        selected_index: selected,
        client_answered_at: new Date().toISOString(),
      }),
    onSuccess: (r) => setCorrectIndex(r.correct_index),
  });

  const finish = useMutation({
    mutationFn: () => quizApi.finish(session!.id),
    onSuccess: (r) => {
      setResult(r);
      setStage("done");
    },
  });

  const restart = () => {
    setSession(null);
    setResult(null);
    setStage("setup");
  };

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
              <IconImage name="checklist" size={34} />
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

  if (stage === "setup") {
    return (
      <Screen>
        <ScreenChrome title={t("quizSetupTitle")} help="quiz" />
        <AppText weight="800" size={12} muted style={{ marginBottom: 10 }}>
          {t("quizCategoryLabel")}
        </AppText>
        <View style={{ flexDirection: row, flexWrap: "wrap", gap: 10, marginBottom: spacing.xl }}>
          {CATEGORIES.map((c) => {
            const sel = category === c.key;
            return (
              <Pressable
                key={c.key}
                onPress={() => setCategory(c.key)}
                style={{
                  width: "47%",
                  padding: 14,
                  borderRadius: 14,
                  backgroundColor: sel ? colors.accent + "1a" : colors.softBg,
                  borderWidth: 1.5,
                  borderColor: sel ? colors.accent : colors.trackBg,
                }}
              >
                <AppText weight={sel ? "800" : "600"} size={13} color={sel ? colors.accent : colors.ink}>
                  {isFa ? c.fa : c.en}
                </AppText>
              </Pressable>
            );
          })}
        </View>

        <AppText weight="800" size={12} muted style={{ marginBottom: 10 }}>
          {t("quizCountLabel")}
        </AppText>
        <View style={{ flexDirection: row, gap: 8, marginBottom: spacing.xl }}>
          {COUNTS.map((c) => {
            const sel = count === c;
            return (
              <Pressable
                key={c}
                onPress={() => setCount(c)}
                style={{
                  flex: 1,
                  height: 46,
                  borderRadius: 12,
                  alignItems: "center",
                  justifyContent: "center",
                  backgroundColor: sel ? colors.accent : colors.softBg,
                  borderWidth: 1.5,
                  borderColor: sel ? colors.accent : colors.trackBg,
                }}
              >
                <AppText weight="800" size={14} color={sel ? colors.onAccent : colors.ink}>
                  {n(c)}
                </AppText>
              </Pressable>
            );
          })}
        </View>

        <Button label={t("quizStartBtn")} onPress={() => start.mutate()} loading={start.isPending} />
      </Screen>
    );
  }

  if (stage === "done" && result) {
    return (
      <Screen>
        <ScreenChrome title={t("quizTitle")} help="quiz" />
        <Card raised style={{ alignItems: "center", paddingVertical: 28 }}>
          <View
            style={{
              width: 72,
              height: 72,
              borderRadius: 36,
              backgroundColor: colors.softBg,
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 14,
            }}
          >
            <IconImage name="graduation" size={40} />
          </View>
          <AppText weight="800" size={20}>
            {t("quizResultTitle")}
          </AppText>
          <AppText weight="900" size={26} color={colors.accent} style={{ marginTop: 8 }}>
            {n(result.score)}/{n(result.total)}
          </AppText>
          <Button label={t("quizRetry")} onPress={restart} style={{ marginTop: 18 }} />
        </Card>
      </Screen>
    );
  }

  // running
  const q = session!.questions[index];
  const options = isFa ? q.options_fa : q.options_en;
  const answered = correctIndex !== null;
  const progress = ((index + (answered ? 1 : 0)) / session!.questions.length) * 100;

  return (
    <Screen>
      <ScreenChrome title={t("quizTitle")} help="quiz" />
      <View style={{ flexDirection: row, alignItems: "center", gap: 8, marginBottom: spacing.lg }}>
        <View style={{ flex: 1, height: 6, borderRadius: 999, backgroundColor: colors.trackBg, overflow: "hidden" }}>
          <View style={{ width: `${progress}%`, height: 6, backgroundColor: colors.accent }} />
        </View>
        <AppText weight="800" size={12} muted>
          {n(index + 1)}/{n(session!.questions.length)}
        </AppText>
      </View>

      <Card>
        <AppText weight="800" size={15} style={{ lineHeight: 26, marginBottom: 16 }}>
          {isFa ? q.prompt_fa : q.prompt_en}
        </AppText>
        <View style={{ gap: 10 }}>
          {options.map((label, i) => {
            let bg = colors.optBg;
            let border = colors.trackBg;
            if (answered && i === correctIndex) {
              bg = colors.accent + "1a";
              border = colors.accent;
            } else if (answered && i === picked && i !== correctIndex) {
              bg = colors.denyBg;
              border = colors.denyBorder;
            }
            return (
              <Pressable
                key={i}
                disabled={answered}
                onPress={() => {
                  setPicked(i);
                  answer.mutate(i);
                }}
                style={{
                  padding: 14,
                  borderRadius: 12,
                  backgroundColor: bg,
                  borderWidth: 1.5,
                  borderColor: border,
                }}
              >
                <AppText weight="600" size={14}>
                  {label}
                </AppText>
              </Pressable>
            );
          })}
        </View>
      </Card>

      {answered ? (
        <Button
          label={index + 1 < session!.questions.length ? t("quizNext") : t("quizResultTitle")}
          onPress={() => {
            if (index + 1 < session!.questions.length) {
              setIndex(index + 1);
              setPicked(null);
              setCorrectIndex(null);
            } else {
              finish.mutate();
            }
          }}
          loading={finish.isPending}
          style={{ marginTop: spacing.lg }}
        />
      ) : null}
    </Screen>
  );
}
