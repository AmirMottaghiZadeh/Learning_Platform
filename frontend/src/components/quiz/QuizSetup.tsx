import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Pressable, TextInput, View } from "react-native";

import { lessonsApi, quizApi } from "@/api/endpoints";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { ICONS, IconImage, IconName } from "@/components/primitives/IconImage";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { TourTarget, useTour } from "@/tour/TourContext";
import { groupByCategory } from "@/utils/lessonCategories";

const COUNTS = [5, 10, 15, 20];
function icon(name: string): IconName {
  return name in ICONS ? name as IconName : "edu-quiz";
}

/** The former deck browser's category grid and topic rows, using the shared
 * clinical taxonomy. Questions stay scoped to the selected topic/chapter. */
export function QuizSetup({ onStart, pending, error, initialSelection, onSelectionChange }: {
  initialSelection?: { category: string; atc_code: string; count: number };
  onSelectionChange: () => void;
  onStart: (topic: string, chapter: string, count: number) => void;
  pending: boolean;
  error?: string;
}) {
  const { t, isFa, n, row } = useLang();
  const { colors, shadows } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const initialTopic = String(useNav((s) => s.params.topic ?? ""));
  const [categoryCode, setCategoryCode] = useState<string | null>(null);
  const [topicCode, setTopicCode] = useState<string | null>(initialSelection?.category || initialTopic || null);
  const [chapter, setChapter] = useState(initialSelection?.atc_code ?? "");
  const [count, setCount] = useState(initialSelection?.count ?? 10);
  const [search, setSearch] = useState("");
  const groups = useQuery({ queryKey: ["lesson-groups"], queryFn: lessonsApi.groups });
  const overview = useQuery({ queryKey: ["quiz-overview"], queryFn: quizApi.overview });
  const categories = useMemo(() => groupByCategory(groups.data ?? []), [groups.data]);
  const topic = groups.data?.find((g) => g.code === topicCode);
  const category = categories.find((c) => c.code === (categoryCode ?? topic?.category_code));
  const preview = useQuery({
    queryKey: ["quiz-preview", topicCode, chapter, count],
    queryFn: () => quizApi.preview(topicCode!, chapter, count),
    enabled: !!topic,
  });
  const back = () => {
    onSelectionChange();
    if (topicCode) { setCategoryCode(topic?.category_code ?? categoryCode); setTopicCode(null); setChapter(""); }
    else if (categoryCode) { setCategoryCode(null); setSearch(""); }
    else goBack();
  };
  useBackInterceptor(!!category || !!topicCode, back);
  useTour("quiz", !category && !groups.isLoading);
  const q = search.trim().toLowerCase();
  const matches = (fa: string, en: string) => !q || `${fa} ${en}`.toLowerCase().includes(q);
  const visibleCategories = categories.filter((c) => matches(c.name_fa, c.name_en) || c.topics.some((tp) => matches(tp.name_fa, tp.name_en)));
  const visibleTopics = category?.topics.filter((tp) => matches(tp.name_fa, tp.name_en)) ?? [];

  return (
    <Screen key={topicCode ?? categoryCode ?? "categories"}>
      <ScreenChrome title={topic ? (isFa ? topic.name_fa : topic.name_en) : category ? (isFa ? category.name_fa : category.name_en) : t("quizSetupTitle")}
        onBack={back} tour={!category ? "quiz" : undefined} help="quiz" />
      {!topic && <>
        {!category && <TourTarget id="quiz.stats">
          <View style={[{ backgroundColor: colors.accent, borderRadius: 22, padding: 16, gap: 10 }, shadows.raisedSm]}>
            <AppText weight="700" size={13} color={colors.onAccent}>
              {isFa ? "یک دسته را باز کن، زیردسته‌ات را انتخاب کن و آزمون بده." : "Open a category, select a topic, then take a quiz."}
            </AppText>
            {overview.data && <AppText size={12} color={colors.onAccentSub}>
              {n(overview.data.total_quizzes)} {t("quizStatTotalQuizzes")} · {t("quizStatAvgScore")} {n(overview.data.avg_score_pct)}٪
            </AppText>}
          </View>
        </TourTarget>}
        <TourTarget id="quiz.search" style={{ marginVertical: 16 }}>
          <TextInput value={search} onChangeText={setSearch} accessibilityLabel={t("quizSearchTopicPlaceholder")}
            placeholder={t("quizSearchTopicPlaceholder")} placeholderTextColor={colors.muted}
            style={{ backgroundColor: colors.inputBg, color: colors.ink, borderRadius: 13, padding: 13, fontFamily: fontFamily("600"), fontSize: 13, textAlign: isFa ? "right" : "left" }} />
        </TourTarget>
      </>}
      {groups.isLoading ? <LoadingState /> : groups.isError ? <Card>
        <AppText color={colors.denyLabel}>{isFa ? "دریافت دسته‌ها انجام نشد." : "Categories could not be loaded."}</AppText>
        <Button label={isFa ? "تلاش دوباره" : "Retry"} onPress={() => { void groups.refetch(); }} />
      </Card> : !topic ? <TourTarget id="quiz.topics">
        <View style={{ flexDirection: category ? "column" : row, flexWrap: category ? "nowrap" : "wrap", gap: 12, width: "100%" }}>
          {!category ? visibleCategories.map((c) => (
            <Pressable key={c.code} accessibilityRole="button" onPress={() => { setCategoryCode(c.code); setSearch(""); }}
              style={[{ width: "47.5%", padding: 14, gap: 8, borderRadius: 20, backgroundColor: colors.cardBg }, shadows.raisedSm]}>
              <IconImage name={icon(`cat-${c.code}`)} size={44} />
              <AppText weight="800" size={14.5}>{isFa ? c.name_fa : c.name_en}</AppText>
              <AppText muted size={12}>{n(c.topics.length)} {isFa ? "زیردسته" : "topics"}</AppText>
            </Pressable>
          )) : visibleTopics.map((tp) => {
            const mastery = overview.data?.mastery[tp.code];
            return <Pressable key={tp.code} accessibilityRole="button" onPress={() => { setTopicCode(tp.code); setChapter(""); onSelectionChange(); }}
              style={{ width: "100%", padding: 14, borderRadius: 20, backgroundColor: colors.cardBg, flexDirection: row, alignItems: "center", gap: 12 }}>
              <IconImage name={icon(`topic-${tp.code}`)} size={40} />
              <View style={{ flex: 1, gap: 4 }}>
                <AppText weight="800" size={15}>{isFa ? tp.name_fa : tp.name_en}</AppText>
                <AppText muted size={12}>{mastery === undefined ? t("quizNewTopic") : `${t("quizMastery")} ${n(mastery)}٪`}</AppText>
              </View>
              <AppText weight="800" size={12} color={colors.accent}>{isFa ? "انتخاب" : "Select"}</AppText>
            </Pressable>;
          })}
        </View>
        {(category ? visibleTopics : visibleCategories).length === 0 && <Card>
          <AppText muted center>{isFa ? "دسته یا زیردسته‌ای پیدا نشد." : "No categories or topics found."}</AppText>
        </Card>}
      </TourTarget> : <Card style={{ gap: 16 }}>
        <AppText muted size={13}>{isFa ? "فصل و تعداد سؤال‌ها را انتخاب کن." : "Choose a chapter and the number of questions."}</AppText>
        <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8 }}>
          <Chip label={t("quizAllChapters")} active={!chapter} onPress={() => { setChapter(""); onSelectionChange(); }} />
          {topic.subgroups.map((sub) => <Chip key={sub.code} label={isFa ? sub.name_fa : sub.name_en} active={chapter === sub.code} onPress={() => { setChapter(sub.code); onSelectionChange(); }} />)}
        </View>
        <AppText weight="800">{t("quizCountLabel")}</AppText>
        <View style={{ flexDirection: row, gap: 8 }}>
          {COUNTS.map((value) => <Chip key={value} label={n(value)} active={count === value} onPress={() => { setCount(value); onSelectionChange(); }} />)}
        </View>
        {preview.isFetching ? <LoadingState /> : preview.isError ? <>
          <AppText color={colors.denyLabel}>{isFa ? "دریافت سؤال‌های این زیردسته انجام نشد." : "Could not load this topic's questions."}</AppText>
          <Button label={isFa ? "تلاش دوباره" : "Retry"} onPress={() => { void preview.refetch(); }} />
        </> : preview.data && <>
          <AppText muted>{n(preview.data.available)} {isFa ? "سؤال در این آزمون" : "questions in this quiz"} · ~{n(preview.data.estimated_minutes)} {t("quizEstimatedMinutes")}</AppText>
          {preview.data.available < count && <AppText color={colors.denyLabel}>{t("quizInsufficientData")}</AppText>}
        </>}
        {error && <AppText color={colors.denyLabel}>{error}</AppText>}
        <Button label={`${t("quizStartBtn")} · ${n(count)}`} loading={pending}
          disabled={!preview.data || preview.isFetching || preview.isError || preview.data.available < count}
          onPress={() => onStart(topic.code, chapter, count)} />
      </Card>}
    </Screen>
  );
}

function Chip({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  const { colors } = useTheme();
  return <Pressable accessibilityRole="button" accessibilityState={{ selected: active }} onPress={onPress}
    style={{ paddingVertical: 10, paddingHorizontal: 14, borderRadius: 12, backgroundColor: active ? colors.accent : colors.softBg }}>
    <AppText weight="700" size={12} color={active ? colors.onAccent : colors.ink}>{label}</AppText>
  </Pressable>;
}
