import { useQuery } from "@tanstack/react-query";
import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, TextInput, View } from "react-native";
import { aiLabApi, LAB_MODEL, LabCitation } from "@/api/aiLab";
import { ApiError } from "@/api/client";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { useNavClearance } from "@/components/BottomNav";
import { useAiLab } from "@/store/aiLab";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { useLang } from "@/i18n/LanguageProvider";
import { fontFamily } from "@/theme/fonts";
import { ReferenceSearchProgress } from "@/components/ReferenceSearchProgress";
import { cancelReferenceTiming, noteReferenceRender, startReferenceTiming } from "@/api/referenceTiming";

const SAMPLE = ["دارودرمانی شب ادراری در کودکان چیست؟", "خط اول درمان پسوریازیس و خط سوم درمان بیماران سایکوتیک"];

function failure(code?: string, status?: number): string {
  if (code === "EXPERIMENT_TIMEOUT") return "مهلت این جست‌وجو تمام شد. می‌توانید دوباره تلاش کنید.";
  if (code === "SEARCH_REQUEST_LIMIT") return "این جست‌وجو به پاسخ کافی نرسید. می‌توانید دوباره تلاش کنید.";
  if (code === "EXPERIMENT_EXPIRED") return "جست‌وجوی قبلی متوقف یا منقضی شد. می‌توانید دوباره سؤال بپرسید.";
  if (code === "PROVIDER_HTTP_ERROR" || code === "PROVIDER_UNAVAILABLE") return "ارتباط با سرویس جست‌وجو برقرار نشد. کمی بعد دوباره تلاش کنید.";
  if (code === "SOURCE_UNAVAILABLE") return "منبع UpToDate در سرور در دسترس نیست.";
  if (code === "INVALID_MODEL_OUTPUT") return "پاسخ قابل استناد دریافت نشد. دوباره تلاش کنید.";
  if (status === 401 || code === "KEY_NOT_CONFIGURED") return "سرویس سرچ هوشمند فعلاً در دسترس نیست.";
  return "جست‌وجو کامل نشد. اتصال را بررسی کنید و دوباره تلاش کنید.";
}

export function AiLabScreen() {
  const { colors } = useTheme();
  const { row, isFa } = useLang();
  const { navigate, goBack } = useNav();
  const userId = useAuth((s) => s.user?.id ?? null);
  const state = useAiLab();
  const clearance = useNavClearance();
  const scroll = useRef<ScrollView>(null);
  const turnPositions = useRef<Record<string, number>>({});
  const sending = useRef(false);
  const [requestError, setRequestError] = useState("");
  const [quotes, setQuotes] = useState<Record<string, boolean>>({});
  const [findingsCollapsed, setFindingsCollapsed] = useState<Record<string, boolean>>({});
  const lastVisible = useRef({ id: "", count: 0 });
  const [recovering, setRecovering] = useState(true);
  const status = useQuery({ queryKey: ["ai-lab-status", userId], queryFn: aiLabApi.status, retry: false, staleTime: 0 });
  const turns = state.owner === userId ? state.turns : [];
  const active = turns.find((t) => t.status === "running");
  const latest = turns[turns.length - 1];
  useEffect(() => {
    if (!latest) return;
    const count = latest.findings?.length ?? 0;
    const previous = lastVisible.current;
    lastVisible.current = { id: latest.id, count };
    const frame = requestAnimationFrame(() => {
      if (latest.status === "running" && !count && previous.id !== latest.id) scroll.current?.scrollToEnd({ animated: true });
      else if ((count > 0 && !previous.count) || (latest.status !== "running" && !previous.count)) {
        scroll.current?.scrollTo({ y: Math.max(0, (turnPositions.current[latest.id] ?? 0) - 8), animated: true });
      }
    });
    return () => cancelAnimationFrame(frame);
  }, [latest?.id, latest?.status, latest?.findings?.length]);
  useEffect(() => { if (useAiLab.getState().owner !== userId) useAiLab.getState().reset(userId); }, [userId]);
  useLayoutEffect(() => {
    if (!latest) return;
    let second = 0;
    const first = requestAnimationFrame(() => {
      second = requestAnimationFrame(() => noteReferenceRender(latest.id, {
        status: latest.status, titles: !!latest.workflow?.some((part) => part.titles.length > 0),
        citation: !!latest.findings?.length || !!latest.result?.parts.some((part) => part.items.length > 0),
        answerComplete: !!latest.result?.parts.length && latest.result.parts.every((part) => part.status === "answered" && part.items.length > 0),
      }));
    });
    return () => { cancelAnimationFrame(first); if (second) cancelAnimationFrame(second); };
  }, [latest?.id, latest?.revision, latest?.status, latest?.result, latest?.findings, latest?.workflow]);
  const restore = useCallback(async () => {
    const job = await aiLabApi.active();
    if (!job || job.model !== LAB_MODEL || useAuth.getState().user?.id !== userId || useAiLab.getState().owner !== userId) return null;
    useAiLab.setState((s) => ({ turns: s.turns.some((t) => t.jobId === job.job_id) ? s.turns : [...s.turns, {
      id: `recovered-${job.job_id}`, jobId: job.job_id, question: job.question, model: job.model, status: "running", stage: job.stage,
      findings: job.findings, revision: job.revision, findings_limited: job.findings_limited, first_result_ms: job.first_result_ms,
      workflow: job.workflow, stages_seen: job.stages_seen,
    }] }));
    return job;
  }, [userId]);
  useEffect(() => {
    let stopped = false;
    setRecovering(true);
    void restore().catch(() => { /* The next send can retry recovery; no duplicate is admitted by the server. */ })
      .finally(() => { if (!stopped) setRecovering(false); });
    return () => { stopped = true; };
  }, [restore]);
  useEffect(() => {
    if (!active?.jobId) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const revision = useAiLab.getState().turns.find((turn) => turn.id === active.id)?.revision;
        const response = await aiLabApi.result(active.jobId!, revision);
        if (stopped || useAuth.getState().user?.id !== userId || useAiLab.getState().owner !== userId) return;
        useAiLab.getState().patch(active.id, response);
        if (response.status === "running") timer = setTimeout(() => void poll(), 1000);
      } catch (error) {
        if (stopped) return;
        if (error instanceof ApiError && [401, 403, 404].includes(error.status)) {
          useAiLab.getState().patch(active.id, { status: "failed", error: { code: "EXPERIMENT_EXPIRED" } });
        } else timer = setTimeout(() => void poll(), 4000);
      }
    };
    void poll();
    return () => { stopped = true; clearTimeout(timer); };
  }, [active?.jobId, userId]);

  const send = async (question = state.draft) => {
    const q = question.trim();
    if (!q || active || recovering || sending.current) return;
    sending.current = true; setRequestError("");
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    startReferenceTiming(id);
    const history = turns.filter((t) => t.question !== q).slice(-4).map((t) => t.question);
    useAiLab.setState((s) => ({ turns: [...s.turns, { id, question: q, model: LAB_MODEL, status: "running", stage: "starting" }], draft: "" }));
    try {
      const job = await aiLabApi.ask(q, history);
      if (useAuth.getState().user?.id === userId && useAiLab.getState().owner === userId) useAiLab.getState().patch(id, { jobId: job.job_id });
    } catch (error) {
      if (!(error instanceof ApiError) || error.code === "AI_LAB_BUSY") {
        try {
          const previous = await restore();
          if (previous) {
            cancelReferenceTiming(id);
            useAiLab.setState((s) => ({ turns: s.turns.filter((t) => t.id !== id), draft: previous.question === q ? "" : q }));
            setRequestError("جست‌وجوی قبلی بازیابی شد؛ نتیجه در همین گفت‌وگو نمایش داده می‌شود.");
            return;
          }
        } catch { /* Keep the submitted question available for retry. */ }
      }
      if (useAiLab.getState().owner === userId) useAiLab.getState().patch(id, { status: "failed", error: { code: "REQUEST_FAILED" } });
      setRequestError(error instanceof ApiError && error.status === 429 ? error.message : "ارسال سؤال انجام نشد؛ سؤال در گفت‌وگو باقی مانده است.");
    } finally { sending.current = false; }
  };

  const open = (citation: LabCitation) => {
    const { screen, params } = citation.target;
    if (screen === "uptodateArticle") navigate("uptodateArticle", params);
  };

  const citationCard = (citation: LabCitation, key: string, overview?: string) => <View testID="reference-citation" key={key} style={{ backgroundColor: colors.softBg, padding: 14, borderRadius: 14, gap: 10 }}>
    {!overview?.includes(citation.summary_fa) ? <AppText size={14}>{citation.summary_fa}</AppText> : null}
    <AppText weight="700" size={12} color={colors.accent}>UpToDate · {citation.section}</AppText>
    <Pressable accessibilityRole="button" accessibilityState={{ expanded: !!quotes[key] }}
      onPress={() => setQuotes((s) => ({ ...s, [key]: !s[key] }))}
      style={{ minHeight: 44, justifyContent: "center" }}>
      <AppText size={13} color={colors.accent}>{quotes[key] ? "بستن بند منبع" : "نمایش بند منبع"}</AppText>
    </Pressable>
    {quotes[key] ? <AppText selectable size={13} style={{ writingDirection: "ltr", textAlign: "left" }}>{citation.quote}</AppText> : null}
    <Pressable accessibilityRole="button" onPress={() => open(citation)} style={{ minHeight: 44, justifyContent: "center" }}>
      <AppText weight="800" size={13} color={colors.accent}>باز کردن متن اصلی</AppText><AppText size={12} muted>{citation.title}</AppText>
    </Pressable>
  </View>;

  return <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={{ flex: 1, backgroundColor: colors.appBg, paddingBottom: clearance }}>
    <View style={{ paddingHorizontal: 20, paddingTop: 12 }}>
      <ScreenChrome title={isFa ? "سرچ هوشمند" : "Smart search"} onBack={goBack} />
      <AppText size={12} muted>UpToDate · پاسخ فارسی و ارجاع مستقیم به بند منبع</AppText>
    </View>
    <ScrollView ref={scroll} contentContainerStyle={{ padding: 20, gap: 18, flexGrow: 1 }}>
      {!turns.length ? <View style={{ gap: 12, paddingTop: 12 }}>
        <AppText weight="800" size={20}>سؤال شما، متن اصلی منبع</AppText>
        <AppText size={14} muted>پرسش خود را بنویسید؛ عنوان مقاله‌ها و بندهای مرتبط، همراه پاسخ فارسی و ارجاع منبع نمایش داده می‌شوند.</AppText>
        {SAMPLE.map((q) => <Pressable key={q} onPress={() => useAiLab.setState({ draft: q })} style={{ minHeight: 48, paddingVertical: 10 }}>
          <AppText size={14} color={colors.accent}>{q}</AppText>
        </Pressable>)}
      </View> : null}
      {status.isError ? <AppText size={13} muted>دریافت وضعیت سرچ هوشمند ممکن نشد. <AppText color={colors.accent} onPress={() => void status.refetch()}>تلاش دوباره</AppText></AppText> : null}
      {status.data && !status.data.enabled ? <AppText size={14} muted>سرچ هوشمند برای حساب شما فعال نیست.</AppText> : null}
      {turns.map((turn) => {
        const finalIds = new Set(turn.result?.parts.flatMap((part, i) => part.items.map((item) => `${i}:${item.target.params.id}:${item.source_id}`)) ?? []);
        const findings = (turn.findings ?? []).filter((finding) => !finalIds.has(finding.id));
        return <View testID={turn.status === "complete" ? "reference-final-answer" : "reference-pending-answer"} key={turn.id} onLayout={(event) => { turnPositions.current[turn.id] = event.nativeEvent.layout.y; }} style={{ gap: 12 }}>
        <View style={{ backgroundColor: colors.accent, borderRadius: 16, padding: 14 }}><AppText color={colors.onAccent} size={14}>{turn.question}</AppText></View>
        <AppText weight="800" size={13}>پاسخ</AppText>
        <ReferenceSearchProgress status={turn.status} stage={turn.stage} seen={turn.stages_seen} workflow={turn.workflow} />
        {turn.status === "failed" ? <AppText size={14} color={colors.denyLabel}>{failure(turn.error?.code, turn.error?.provider_status)}</AppText> : null}
        {turn.result?.parts.length === 0 ? <AppText size={14} muted>در محدودهٔ منابع انتخاب‌شده پاسخی پیدا نشد.</AppText> : null}
        {turn.result?.parts.map((part, i) => <View key={i} style={{ gap: 10 }}>
          <AppText weight="700" size={14}>{part.question_fa}</AppText>
          {part.overview_fa ? <AppText size={14}>{part.overview_fa}</AppText> : null}
          {part.items.length ? <AppText size={12} muted>{part.items.length} ارجاع از {part.retrieval?.reviewed_passages ?? part.retrieval?.selected_passages ?? part.items.length} متن بررسی‌شده</AppText> : null}
          {part.retrieval?.early_stopped ? <AppText size={12} muted>{part.retrieval.reviewed_articles ?? 1} مقاله بررسی شد؛ پس از یافتن پاسخ کافی، بررسی مقاله‌های بعدی متوقف شد.</AppText> : null}
          {part.retrieval?.limited && !part.retrieval.early_stopped ? <AppText size={12} muted>نمایش نتایج بازیابی‌شده در محدودهٔ این جست‌وجو؛ پوشش منابع کامل نیست.</AppText> : null}
          {part.status === "partial" ? <AppText size={13} muted>{part.clarification_fa || "این مقاله فقط بخشی از سؤال را پوشش می‌دهد؛ پاسخ کامل تأیید نشد."}</AppText> : null}
          {part.status === "needs_clarification" ? <AppText size={14}>{part.clarification_fa}</AppText> : null}
          {part.status === "not_found" ? <AppText size={14} muted>متن کافی برای پاسخ مستند پیدا نشد؛ پاسخی حدس زده نشد.</AppText> : null}
          {part.items.map((citation) => citationCard(citation, `${turn.id}:${i}:${citation.target.params.id}:${citation.source_id}`, part.overview_fa))}
        </View>)}
        {findings.length ? <View style={{ gap: 10 }}>
          <AppText size={13} weight="700">{turn.status === "running" ? "نتایج بررسی‌شده تا این لحظه" : turn.status === "failed" ? "نتایج دریافت‌شده پیش از توقف" : "شواهد جزئیِ دیگر هنگام بررسی"}</AppText>
          <AppText size={12} muted>{turn.status === "complete" ? "این شواهد در پاسخ نهایی انتخاب نشدند و برای مرور باقی مانده‌اند." : "این بندها بررسی شده‌اند؛ کافی بودن پاسخ کامل هنوز مشخص نشده است."}</AppText>
          {turn.status === "complete" ? <Pressable accessibilityRole="button" accessibilityState={{ expanded: !findingsCollapsed[turn.id] }}
            onPress={() => setFindingsCollapsed((s) => ({ ...s, [turn.id]: !s[turn.id] }))} style={{ minHeight: 44, justifyContent: "center" }}>
            <AppText size={13} color={colors.accent}>{findingsCollapsed[turn.id] ? "نمایش شواهد قبلی" : "بستن شواهد قبلی"}</AppText>
          </Pressable> : null}
          {turn.status !== "complete" || !findingsCollapsed[turn.id] ? findings.map((finding, i) => <View key={finding.id} style={{ gap: 8 }}>
            {i === 0 || findings[i - 1].part_index !== finding.part_index ? <AppText size={13} weight="700">{finding.question_fa}</AppText> : null}
            {citationCard(finding.citation, `${turn.id}:${finding.id}`)}
          </View>) : null}
        </View> : null}
        {turn.findings_limited ? <AppText size={12} muted>سقف نمایش تدریجی پر شده است؛ بررسی ادامه یافته و نتیجهٔ نهایی جداگانه نمایش داده می‌شود.</AppText> : null}
        {turn.first_result_ms !== undefined ? <AppText size={12} muted>زمان اولین نتیجه: {(turn.first_result_ms / 1000).toFixed(1)} ثانیه</AppText> : null}
        {turn.result ? <AppText muted size={12}>زمان جست‌وجو: {(turn.result.elapsed_ms / 1000).toFixed(1)} ثانیه</AppText> : null}
        {turn.result?.warnings.length ? <AppText muted size={12}>برخی منابع یا توضیح‌ها قابل تأیید نبودند و کنار گذاشته شدند.</AppText> : null}
        {turn.status === "failed" ? <Pressable disabled={!!active} onPress={() => void send(turn.question)} style={{ minHeight: 44, justifyContent: "center" }}><AppText size={13} muted>تلاش دوباره</AppText></Pressable> : null}
      </View>; })}
    </ScrollView>
    {requestError ? <AppText size={12} color={colors.denyLabel} style={{ paddingHorizontal: 20 }}>{requestError}</AppText> : null}
    {recovering ? <AppText size={12} muted style={{ paddingHorizontal: 20 }}>بررسی درخواست قبلی…</AppText> : null}
    <View style={{ padding: 12, gap: 10, flexDirection: row, alignItems: "flex-end", backgroundColor: colors.cardBg }}>
      <TextInput testID="reference-question" value={state.draft} onChangeText={(draft) => useAiLab.setState({ draft })} multiline maxLength={1500} editable={!active}
        accessibilityLabel="پرسش برای سرچ هوشمند" placeholder="سؤال خود را بنویسید…" placeholderTextColor={colors.muted}
        style={{ flex: 1, minHeight: 48, maxHeight: 120, padding: 12, borderRadius: 12, backgroundColor: colors.softBg,
          fontFamily: fontFamily("500"), fontSize: 14, color: colors.ink, textAlign: isFa ? "right" : "left" }} />
      <Pressable testID="reference-send" accessibilityRole="button" onPress={() => void send()} disabled={recovering || !!active || !status.data?.enabled || !state.draft.trim()}
        style={{ minHeight: 48, paddingHorizontal: 18, justifyContent: "center", borderRadius: 12, backgroundColor: colors.accent,
          opacity: recovering || active || !status.data?.enabled || !state.draft.trim() ? 0.5 : 1 }}>
        <AppText weight="800" color={colors.onAccent}>{active ? "…" : "جست‌وجو"}</AppText>
      </Pressable>
    </View>
  </KeyboardAvoidingView>;
}
