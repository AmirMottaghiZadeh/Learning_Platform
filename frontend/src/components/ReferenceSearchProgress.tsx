import React, { useState } from "react";
import { ActivityIndicator, Pressable, View } from "react-native";
import type { LabJob, LabWorkflowPart } from "@/api/aiLab";
import { useTheme } from "@/theme/ThemeProvider";
import { useLang } from "@/i18n/LanguageProvider";
import { AppText } from "@/components/primitives/AppText";

const STEPS = [
  { label: "فهم پرسش", stages: ["starting", "planning"] },
  { label: "عنوان مقاله", stages: ["retrieving"] },
  { label: "زیربخش", stages: ["reading_article", "selecting_sections"] },
  { label: "بند منبع", stages: ["answering"] },
  { label: "پاسخ", stages: ["verifying"] },
];
const DETAILS: Record<string, string> = {
  starting: "جست‌وجوی شما در حال شروع است…", planning: "در حال فهم پرسش و مشخص کردن موضوع جست‌وجو…",
  retrieving: "در حال پیدا کردن عنوان مقاله‌های مرتبط…", reading_article: "در حال باز کردن مقاله و شناسایی زیربخش‌ها…",
  selecting_sections: "در حال پیدا کردن زیربخش‌های مرتبط در مقاله…", answering: "در حال خواندن بندهای مرتبط و آماده کردن پاسخ فارسی…",
  verifying: "در حال بررسی پاسخ فارسی با متن اصلی منبع…",
};
const OUTCOMES: Record<string, string> = { answered: "منبع پاسخ", partial: "پاسخ جزئی", no_answer: "پاسخ کافی یافت نشد", directory: "فهرست دارو؛ بررسی تاپیک‌های مرتبط" };

export function ReferenceSearchProgress({ status, stage = "starting", seen, workflow = [] }: {
  status: LabJob["status"]; stage?: string; seen?: string[]; workflow?: LabWorkflowPart[];
}) {
  const { colors } = useTheme();
  const { row } = useLang();
  const [expanded, setExpanded] = useState(false);
  const [allTitles, setAllTitles] = useState<Record<number, boolean>>({});
  const [allSections, setAllSections] = useState<Record<string, boolean>>({});
  const running = status === "running";
  const open = status !== "complete" || expanded;
  const visited = new Set(seen ?? [stage]);
  const active = running ? STEPS.findIndex((step) => step.stages.includes(stage)) : -1;
  const titleCount = workflow.reduce((sum, part) => sum + part.titles.length, 0);
  const reviewed = workflow.reduce((sum, part) => sum + part.articles.reduce((n, article) => n + article.reviewed_passages, 0), 0);

  return <View style={{ backgroundColor: colors.cardBg, borderRadius: 18, padding: 16, gap: 16 }}>
    <Pressable accessibilityRole="button" accessibilityState={{ expanded: open, disabled: running }} disabled={status !== "complete"}
      onPress={() => setExpanded((value) => !value)} style={{ minHeight: 44, gap: 6, justifyContent: "center" }}>
      <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <AppText size={14} weight="800">روند پیدا کردن پاسخ</AppText>
        <AppText size={11} color={running ? colors.accent : colors.muted} accessibilityLiveRegion="polite">
          {running ? "در حال جست‌وجو" : status === "failed" ? "بررسی متوقف شد" : open ? "بستن مراحل" : "مشاهده مراحل"}
        </AppText>
      </View>
      {!open ? <AppText size={12} muted>{titleCount} عنوان پیدا شد · {reviewed} بند بررسی شد</AppText> : null}
    </Pressable>
    {open ? <>
      <View style={{ flexDirection: row, gap: 4 }}>
        {STEPS.map((step, index) => {
          const current = active === index;
          const done = !current && step.stages.some((name) => visited.has(name));
          return <View key={step.label} style={{ flex: 1, alignItems: "center", gap: 7 }}>
            <View style={{ width: 30, height: 30, borderRadius: 15, alignItems: "center", justifyContent: "center",
              backgroundColor: done ? colors.accent : colors.softBg, borderWidth: current ? 1.5 : 0, borderColor: colors.accent }}>
              {current ? <ActivityIndicator size="small" color={colors.accent} /> : <AppText size={12} weight="700" color={done ? colors.onAccent : colors.muted}>{done ? "✓" : index + 1}</AppText>}
            </View>
            <AppText size={10} weight={current ? "800" : "500"} color={current ? colors.accent : colors.muted} style={{ textAlign: "center" }}>{step.label}</AppText>
          </View>;
        })}
      </View>
      {running ? <AppText size={13} color={colors.accent} accessibilityLiveRegion="polite">{DETAILS[stage] ?? "جست‌وجو در حال انجام است…"}</AppText> : null}
      {!workflow.some((part) => part.queries.length) && running ? <View style={{ gap: 12, padding: 14, backgroundColor: colors.softBg, borderRadius: 12 }}>
        <AppText size={12} muted>عنوان مقاله‌ها پس از پیدا شدن، اینجا نمایش داده می‌شود.</AppText>
        {["92%", "76%", "58%"].map((width) => <View key={width} style={{ width: width as `${number}%`, height: 7, borderRadius: 4, backgroundColor: colors.muted, opacity: 0.13 }} />)}
      </View> : null}
      {workflow.map((part) => {
        const currentArticle = part.articles.find((article) => article.id === part.current_article_id);
        const compactTitles = currentArticle?.sections !== undefined;
        const visibleTitles = allTitles[part.part_index] ? part.titles
          : part.titles.filter((title, i) => (!compactTitles && i < 3) || title.id === part.current_article_id);
        const sectionKey = `${part.part_index}:${currentArticle?.id}`;
        const sections = currentArticle?.sections;
        return <View key={part.part_index} style={{ gap: 12 }}>
          {workflow.length > 1 ? <AppText size={13} weight="700">{part.question_fa}</AppText> : null}
          {part.queries.length ? <View style={{ gap: 10 }}>
            <AppText size={13} weight="700">{part.titles.length ? `${part.titles.length} عنوان مقاله پیدا شد` : "برای این عبارت عنوانی پیدا نشد"}</AppText>
            {visibleTitles.map((title) => {
              const article = part.articles.find((item) => item.id === title.id);
              const checking = running && title.id === part.current_article_id && article && !OUTCOMES[article.phase];
              return <View key={title.id} style={{ gap: 7, padding: 12, borderRadius: 12, backgroundColor: colors.softBg,
                borderWidth: checking ? 1 : 0, borderColor: colors.accent }}>
                <AppText size={12} weight="700" style={{ writingDirection: "ltr", textAlign: "left" }}>{title.title}</AppText>
                {title.related_to ? <AppText size={11} muted>تاپیک مرتبط از فهرست اطلاعات دارویی</AppText> : null}
                <View style={{ flexDirection: row, alignItems: "center", gap: 6 }}>
                  {checking ? <ActivityIndicator size="small" color={colors.accent} /> : null}
                  <AppText size={11} color={checking || article?.phase === "answered" ? colors.accent : colors.muted}>
                    {checking ? "در حال بررسی این مقاله" : article && OUTCOMES[article.phase] ? OUTCOMES[article.phase] : running ? "هنوز بررسی نشده" : "بررسی نشد"}
                  </AppText>
                </View>
              </View>;
            })}
            {part.titles.length > (compactTitles ? 1 : 3) ? <Pressable accessibilityRole="button" accessibilityState={{ expanded: !!allTitles[part.part_index] }}
              onPress={() => setAllTitles((values) => ({ ...values, [part.part_index]: !values[part.part_index] }))} style={{ minHeight: 40, justifyContent: "center" }}>
              <AppText size={12} color={colors.accent}>{allTitles[part.part_index] ? "نمایش عنوان‌های کمتر" : `مشاهده همهٔ ${part.titles.length} عنوان`}</AppText>
            </Pressable> : null}
          </View> : null}
          {currentArticle ? <View style={{ gap: 10, paddingTop: 4 }}>
            <AppText size={13} weight="700">زیربخش‌های مرتبط در مقاله</AppText>
            {sections === undefined ? <AppText size={12} muted>{currentArticle.phase === "directory" ? "فهرست دارو باز شد؛ بررسی در متن تاپیک مرتبط ادامه می‌یابد." : running ? "زیربخش‌ها در حال شناسایی هستند…" : "بررسی زیربخش‌ها کامل نشد."}</AppText>
              : !sections.length ? <AppText size={12} muted>زیربخش مرتبطی برای این پرسش پیدا نشد.</AppText>
              : <>
                {(allSections[sectionKey] ? sections : sections.slice(0, 2)).map((section) => <View key={section.id} style={{ padding: 10, borderRadius: 10, backgroundColor: colors.softBg }}>
                  <AppText size={12} style={{ writingDirection: "ltr", textAlign: "left" }}>{section.heading || "متن آغاز مقاله"}</AppText>
                </View>)}
                {sections.length > 2 ? <Pressable accessibilityRole="button" onPress={() => setAllSections((values) => ({ ...values, [sectionKey]: !values[sectionKey] }))} style={{ minHeight: 40, justifyContent: "center" }}>
                  <AppText size={12} color={colors.accent}>{allSections[sectionKey] ? "نمایش زیربخش‌های کمتر" : `مشاهده همهٔ ${sections.length} زیربخش`}</AppText>
                </Pressable> : null}
              </>}
            {currentArticle.paragraph_count !== undefined && currentArticle.paragraph_count > 0 ? <View style={{ padding: 12, borderRadius: 12, backgroundColor: colors.softBg, gap: 6 }}>
              <AppText size={12} weight="700">بندهای منبع</AppText>
              <AppText size={12} muted>{currentArticle.reviewed_passages} بند از {currentArticle.paragraph_count} بند مرتبط بررسی شد.</AppText>
              {running && currentArticle.reviewing_count > 0 ? <AppText size={12} color={colors.accent}>{currentArticle.reviewing_count} بند در حال بررسی است…</AppText> : null}
              {currentArticle.phase === "answered" ? <AppText size={12} color={colors.accent}>پاسخ کافی در همین مقاله پیدا شد.</AppText> : null}
            </View> : null}
          </View> : null}
        </View>;
      })}
    </> : null}
  </View>;
}
