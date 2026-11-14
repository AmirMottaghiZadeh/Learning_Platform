import { useQuery } from "@tanstack/react-query";
import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, TextInput, View } from "react-native";
import { aiLabApi, LAB_MODEL, LabCitation } from "@/api/aiLab";
import { ApiError } from "@/api/client";
import { searchWalletApi } from "@/api/searchWallet";
import { ChromeButton, LangToggleButton } from "@/components/ScreenChrome";
import { ThemeToggleButton } from "@/components/ThemeToggleButton";
import { AppText } from "@/components/primitives/AppText";
import { useNavClearance } from "@/components/BottomNav";
import { useAiLab } from "@/store/aiLab";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { useLang } from "@/i18n/LanguageProvider";
import { fontFamily } from "@/theme/fonts";
import { SearchFeedback } from "@/components/SearchFeedback";
import { SmartSearchWallet } from "@/components/SmartSearchWallet";
import { ReferenceMediaCards } from "@/components/ReferenceMediaCards";
import { HeaderMesh } from "@/components/HeaderMesh";
import { ReferenceAnswerSkeleton, ReferenceSearchLoading } from "@/components/ReferenceSearchLoading";
import { cancelReferenceTiming, noteReferenceRender, startReferenceTiming } from "@/api/referenceTiming";

const SAMPLE = ["دارودرمانی شب ادراری در کودکان چیست؟", "خط اول درمان پسوریازیس و خط سوم درمان بیماران سایکوتیک"];

function failure(code?: string, status?: number): string {
  if (code === "AI_CREDIT_INSUFFICIENT") return "اعتبار سرچ هوشمند کافی نیست؛ از بخش مدیریت اعتبار، حساب خود را شارژ کنید.";
  if (code === "EXPERIMENT_TIMEOUT") return "مهلت این جست‌وجو تمام شد. می‌توانید دوباره تلاش کنید.";
  if (code === "SEARCH_REQUEST_LIMIT") return "این جست‌وجو به پاسخ کافی نرسید. می‌توانید دوباره تلاش کنید.";
  if (code === "EXPERIMENT_EXPIRED") return "جست‌وجوی قبلی متوقف یا منقضی شد. می‌توانید دوباره سؤال بپرسید.";
  if (code === "PROVIDER_HTTP_ERROR" || code === "PROVIDER_UNAVAILABLE") return "ارتباط با سرویس جست‌وجو برقرار نشد. کمی بعد دوباره تلاش کنید.";
  if (code === "REFERENCE_INDEX_NOT_READY" || code === "REFERENCE_INDEX_STALE") return "منبع سرچ هوشمند باید در سرور آماده‌سازی شود. کمی بعد دوباره تلاش کنید.";
  if (code === "SOURCE_UNAVAILABLE") return "منبع UpToDate در سرور در دسترس نیست.";
  if (code === "HYBRID_INDEX_NOT_READY" || code === "HYBRID_INDEX_STALE") return "نمایهٔ سرچ هوشمند هنوز آماده نیست. کمی بعد دوباره تلاش کنید.";
  if (code === "SEARCH_CANCELLED") return "جست‌وجو به درخواست شما متوقف شد.";
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
  const followResults = useRef(true);
  const turnPositions = useRef<Record<string, number>>({});
  const answerPositions = useRef<Record<string, number>>({});
  const mediaPositions = useRef<Record<string, number>>({});
  const sending = useRef(false);
  const [requestError, setRequestError] = useState("");
  const [quotes, setQuotes] = useState<Record<string, boolean>>({});
  const [sourcesExpanded, setSourcesExpanded] = useState<Record<string, boolean>>({});
  const lastVisible = useRef({ id: "" });
  const [recovering, setRecovering] = useState(true);
  const status = useQuery({ queryKey: ["ai-lab-status", userId], queryFn: aiLabApi.status, retry: false, staleTime: 0 });
  const credits=useQuery({queryKey:["ai-search-wallet",userId],queryFn:searchWalletApi.summary,enabled:userId!==null,retry:false,staleTime:10000});
  const creditBlocked=credits.data?.can_search===false;
  const turns = state.owner === userId ? state.turns : [];
  const active = turns.find((t) => t.status === "running");
  const latest = turns[turns.length - 1];
  useEffect(() => {
    if (!latest) return;
    const previous = lastVisible.current;
    lastVisible.current = { id: latest.id };
    const frame = requestAnimationFrame(() => {
      if (latest.status === "running" && previous.id !== latest.id) {
        followResults.current = true;
        scroll.current?.scrollToEnd({ animated: true });
      } else if (latest.status !== "running" && followResults.current) {
        scroll.current?.scrollTo({ y: Math.max(0, (turnPositions.current[latest.id] ?? 0) + (mediaPositions.current[latest.id] ?? answerPositions.current[latest.id] ?? 0) - 8), animated: true });
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
        status: latest.status, titles: !!latest.findings?.some((finding) => finding.citation.title)
          || !!latest.result?.parts.some((part) => part.items.some((item) => item.title)),
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
    const controller = new AbortController();
    let sequence: number | undefined;
    let streaming = true;
    const current = () => !controller.signal.aborted && useAuth.getState().user?.id === userId && useAiLab.getState().owner === userId;
    const follow = async () => {
      while (current()) {
        try {
          if (streaming) await aiLabApi.stream(active.jobId!, sequence, controller.signal, (event) => {
            if (!current()) return;
            if (event.type !== "snapshot" && sequence !== undefined && event.sequence <= sequence) return;
            sequence = event.sequence;
            const turn = useAiLab.getState().turns.find((t) => t.id === active.id);
            if (!turn) return;
            if (event.type === "snapshot" || event.type === "complete") useAiLab.getState().patch(active.id, event.job);
            else if (event.type === "sources") {
              const findings = new Map((turn.findings ?? []).map((item) => [item.id, item]));
              for (const item of event.findings) findings.set(item.id, item);
              useAiLab.getState().patch(active.id, { findings: [...findings.values()] });
            } else if (event.type === "answer_delta" || event.type === "answer_reset") {
              const key = String(event.part_index);
              useAiLab.getState().patch(active.id, { answer_drafts: { ...turn.answer_drafts,
                [key]: event.type === "answer_reset" ? "" : (turn.answer_drafts?.[key] ?? "") + event.text } });
            }
          });
          if (!current()) return;
          // Poll is also the recovery path when a stream ends without a final
          // event. It never resubmits the original, paid question.
          const response = await aiLabApi.result(active.jobId!);
          if (!current()) return;
          useAiLab.getState().patch(active.id, response);
          if (response.status !== "running") return;
        } catch (error) {
          if (!current()) return;
          if (error instanceof ApiError && [401, 403, 404].includes(error.status)) {
            useAiLab.getState().patch(active.id, { status: "failed", error: { code: "EXPERIMENT_EXPIRED" } });
            return;
          }
          streaming = !(error instanceof ApiError && error.code === "STREAM_UNAVAILABLE");
          try {
            const response = await aiLabApi.result(active.jobId!);
            if (!current()) return;
            useAiLab.getState().patch(active.id, response);
            if (response.status !== "running") return;
          } catch { /* Retry the same job after a temporary transport outage. */ }
        }
        await new Promise<void>((resolve) => {
          const done = () => { clearTimeout(timer); controller.signal.removeEventListener("abort", done); resolve(); };
          const timer = setTimeout(done, 1000);
          controller.signal.addEventListener("abort", done, { once: true });
        });
      }
    };
    void follow();
    return () => controller.abort();
  }, [active?.jobId, userId]);

  const send = async (question = state.draft) => {
    const q = question.trim();
    if (!q || active || recovering || sending.current) return;
    if(creditBlocked){setRequestError(failure("AI_CREDIT_INSUFFICIENT"));return;}
    sending.current = true; setRequestError("");
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    startReferenceTiming(id);
    const history = turns.filter((t) => t.question !== q).slice(-4).map((t) => t.question);
    useAiLab.setState((s) => ({ turns: [...s.turns, { id, question: q, model: LAB_MODEL, status: "running", stage: "starting" }], draft: "" }));
    try {
      const job = await aiLabApi.ask(q, history, id);
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
      if (useAiLab.getState().owner === userId) useAiLab.getState().patch(id, { status: "failed", error: { code: error instanceof ApiError ? error.code : "REQUEST_FAILED" } });
      setRequestError(error instanceof ApiError && [402, 429].includes(error.status) ? error.message : "ارسال سؤال انجام نشد؛ سؤال در گفت‌وگو باقی مانده است.");
    } finally { sending.current = false; }
  };

  const open = (citation: LabCitation) => {
    const { screen, params } = citation.target;
    if (screen === "uptodateArticle") navigate("uptodateArticle", params);
  };

  const citationCard = (citation: LabCitation, key: string) => <View testID="reference-citation" key={key} style={{ backgroundColor: colors.softBg, padding: 14, borderRadius: 14, gap: 10 }}>
    {citation.summary_fa ? <AppText size={14}>{citation.summary_fa}</AppText> : <AppText size={12} muted>{isFa ? "بخش مرتبط از منبع" : "Related source passage"}</AppText>}
    <AppText weight="700" size={12} color={colors.accent}>UpToDate · {citation.section}</AppText>
    <Pressable accessibilityRole="button" accessibilityState={{ expanded: !!quotes[key] }}
      onPress={() => setQuotes((s) => ({ ...s, [key]: !s[key] }))}
      style={{ minHeight: 44, justifyContent: "center" }}>
      <AppText size={13} color={colors.accent}>{quotes[key] ? "بستن بند منبع" : "نمایش بند منبع"}</AppText>
    </Pressable>
    {quotes[key] ? <View style={{ gap: 8 }}>
      {citation.context?.length ? <View style={{ gap: 4 }}>
        <AppText size={11} muted>{isFa ? "برچسب‌های پیش از این بند در متن اصلی" : "Preceding labels in the original source"}</AppText>
        <AppText selectable muted size={12} style={{ writingDirection: "ltr", textAlign: "left" }}>{citation.context.map(label => label.quote).join("\n")}</AppText>
      </View> : null}
      <AppText selectable size={13} style={{ writingDirection: "ltr", textAlign: "left" }}>{citation.quote}</AppText>
    </View> : null}
    <Pressable accessibilityRole="button" onPress={() => open(citation)} style={{ minHeight: 44, justifyContent: "center" }}>
      <AppText weight="800" size={13} color={colors.accent}>باز کردن متن اصلی</AppText><AppText size={12} muted>{citation.title}</AppText>
    </Pressable>
  </View>;

  return <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={{ flex: 1, backgroundColor: colors.appBg, paddingBottom: clearance }}>
    <View style={{height:94}}><HeaderMesh><View style={{ paddingHorizontal:20,paddingTop:14,gap:8 }}>
      <View style={{flexDirection:row,alignItems:"center",gap:10}}>
        <ChromeButton onPress={goBack}><AppText weight="800" size={18}>{isFa ? "›" : "‹"}</AppText></ChromeButton>
        <AppText accessibilityRole="header" aria-level={1} color="#FFFFFF" weight="800" size={17} style={{flex:1}}>{isFa ? "سرچ هوشمند" : "Smart search"}</AppText>
        <ThemeToggleButton variant="soft" size={30} /><LangToggleButton />
      </View>
      <AppText size={11} color="rgba(255,255,255,0.8)">{isFa ? "پرسش شما، با پشتوانهٔ منابع بالینی" : "Your questions, supported by clinical references"}</AppText>
    </View></HeaderMesh></View>
    <View style={{paddingHorizontal:20,paddingTop:12}}>
      <SmartSearchWallet compact refreshKey={`${latest?.jobId ?? ""}:${latest?.status ?? ""}`} running={!!active} />
    </View>
    <ScrollView ref={scroll} scrollEventThrottle={100}
      onScroll={({ nativeEvent }) => {
        followResults.current = nativeEvent.contentSize.height - nativeEvent.contentOffset.y - nativeEvent.layoutMeasurement.height < 96;
      }}
      onContentSizeChange={() => {
        if (latest?.status === "running" && followResults.current) scroll.current?.scrollToEnd({ animated: true });
      }} contentContainerStyle={{ padding: 20, gap: 18, flexGrow: 1 }}>
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
        const hasFinalSources = !!turn.result?.parts.some((part) => part.items.length);
        const citations = turn.result?.parts.flatMap((part) => part.items)
          ?? (turn.status === "running" ? (turn.findings ?? []).map((finding) => finding.citation) : []);
        const articles = new Map<string, LabCitation>();
        for (const citation of citations) {
          const articleId = String(citation.target.params.id);
          if (!articles.has(articleId)) articles.set(articleId, citation);
        }
        const hasSources = articles.size > 0;
        return <View testID={turn.status === "complete" ? "reference-final-answer" : "reference-pending-answer"} key={turn.id} onLayout={(event) => { turnPositions.current[turn.id] = event.nativeEvent.layout.y; }} style={{ gap: 12 }}>
        <View style={{backgroundColor:colors.accent,borderRadius:18,padding:14,maxWidth:"95%",alignSelf:isFa ? "flex-end" : "flex-start"}}><AppText color={colors.onAccent} size={14}>{turn.question}</AppText></View>
        {citations.some(c => c.media?.length) ? <View testID="reference-primary-media" onLayout={event=>{mediaPositions.current[turn.id]=event.nativeEvent.layout.y;}} style={{padding:16,borderRadius:18,backgroundColor:colors.cardBg}}>
          <ReferenceMediaCards items={[...new Map(citations.flatMap(c => c.media??[]).map(item => [item.article_id+":"+item.key,item])).values()]} />
        </View> : null}
        <View testID="reference-answer-summary" onLayout={(event) => { answerPositions.current[turn.id] = event.nativeEvent.layout.y; }}
          style={{ backgroundColor: colors.cardBg, borderWidth: 1, borderColor: colors.border, borderRadius: 16, padding: 16, gap: 14 }}>
          <AppText weight="800" size={14}>{isFa ? "پاسخ فارسی" : "Answer"}</AppText>
          {turn.status === "running" ? <ReferenceAnswerSkeleton /> : null}
          {turn.status === "running" && Object.values(turn.answer_drafts ?? {}).some(Boolean) ? <View style={{ gap: 8 }}>
            <AppText muted size={12}>{isFa ? "پیش‌نویس در حال بررسی" : "Draft under review"}</AppText>
            <AppText selectable size={14}>{Object.values(turn.answer_drafts ?? {}).join("\n\n")}</AppText>
          </View> : null}
          {turn.status === "failed" ? <AppText size={14} color={colors.denyLabel}>{failure(turn.error?.code, turn.error?.provider_status)}</AppText> : null}
          {turn.result?.parts.length === 0 ? <AppText size={14} muted>در محدودهٔ منابع انتخاب‌شده پاسخی پیدا نشد.</AppText> : null}
          {turn.result?.parts.map((part, i) => {
            const summary = part.overview_fa || [...new Set(part.items.map((item) => item.summary_fa))].join("\n\n");
            return <View key={i} style={{ gap: 10 }}>
              {turn.result!.parts.length > 1 ? <AppText weight="700" size={14}>{part.question_fa}</AppText> : null}
              {summary ? <AppText testID="reference-answer-text" selectable size={14}>{summary}</AppText> : null}
              {part.retrieval?.limited && !part.retrieval.early_stopped ? <AppText size={12} muted>نمایش نتایج بازیابی‌شده در محدودهٔ این جست‌وجو؛ پوشش منابع کامل نیست.</AppText> : null}
              {part.status === "partial" ? <AppText size={13} muted>{part.clarification_fa || "این منابع فقط بخشی از سؤال را پوشش می‌دهند؛ پاسخ کامل تأیید نشد."}</AppText> : null}
              {part.status === "needs_clarification" ? <AppText size={14}>{part.clarification_fa}</AppText> : null}
              {part.status === "not_found" ? <AppText size={14} muted>متن کافی برای پاسخ مستند پیدا نشد؛ پاسخی حدس زده نشد.</AppText> : null}
            </View>;
          })}
        </View>
        {hasSources ? <View testID="reference-source-results" style={{ gap: 12 }}>
          <AppText weight="800" size={13}>{isFa ? turn.status === "running" ? "منابع در حال بررسی" : "منابع اصلی" : turn.status === "running" ? "Sources under review" : "Sources"}</AppText>
          {[...articles.values()].map((citation,index) => {
            return <View key={String(citation.target.params.id)} style={{padding:16,borderRadius:18,backgroundColor:colors.cardBg,gap:12}}>
              <Pressable testID="reference-source" accessibilityRole="button" onPress={() => open(citation)} style={{flexDirection:row,gap:10,alignItems:"center"}}>
                <View style={{width:28,height:28,borderRadius:9,backgroundColor:colors.leitnerActiveBg,alignItems:"center",justifyContent:"center"}}><AppText weight="800" size={12} color={colors.accent}>{index+1}</AppText></View>
                <View style={{flex:1,gap:5}}><AppText size={11} muted>UpToDate</AppText><AppText weight="800" size={13} style={{writingDirection:"ltr",textAlign:"left"}}>{citation.title}</AppText></View>
              </Pressable>
            </View>;
          })}
          {hasFinalSources ? <View style={{ borderWidth: 1, borderColor: colors.border, borderRadius: 14, overflow: "hidden", backgroundColor: colors.cardBg }}>
            <Pressable testID="reference-sources-toggle" accessibilityRole="button"
              accessibilityLabel={isFa ? "دیدن بخش‌های مرتبط در منابع" : "View relevant source passages"}
              aria-expanded={!!sourcesExpanded[turn.id]}
              accessibilityState={{ expanded: !!sourcesExpanded[turn.id] }}
              onPress={() => setSourcesExpanded((s) => ({ ...s, [turn.id]: !s[turn.id] }))}
              style={{ minHeight: 52, padding: 14, flexDirection: row, alignItems: "center", gap: 12 }}>
              <AppText weight="700" size={13} style={{ flex: 1 }}>{isFa ? "دیدن بخش‌های مرتبط در منابع" : "View relevant source passages"}</AppText>
              <AppText color={colors.accent} size={18}>{sourcesExpanded[turn.id] ? "−" : "+"}</AppText>
            </Pressable>
            {sourcesExpanded[turn.id] ? <View testID="reference-source-passages" style={{ padding: 12, paddingTop: 0, gap: 10 }}>
              {turn.result?.parts.map((part, i) => part.items.length ? <View key={i} style={{ gap: 10 }}>
                {turn.result!.parts.length > 1 ? <AppText weight="700" size={13}>{part.question_fa}</AppText> : null}
                {part.items.map((citation) => citationCard(citation, `${turn.id}:${i}:${citation.target.params.id}:${citation.source_id}`))}
              </View> : null)}
            </View> : null}
          </View> : null}
        </View> : null}
        {turn.status === "running" ? <View style={{ gap: 12 }}>
          <ReferenceSearchLoading hasResults={hasSources} />
          {turn.jobId && turn.cancellable ? <Pressable accessibilityRole="button" onPress={() => {
            void aiLabApi.cancel(turn.jobId!).catch(() => setRequestError("لغو درخواست انجام نشد؛ دوباره تلاش کنید."));
          }} style={{ minHeight: 44, justifyContent: "center" }}><AppText size={13} color={colors.denyLabel}>{isFa ? "توقف جست‌وجو" : "Stop search"}</AppText></Pressable> : null}
        </View> : null}
        {turn.status === "complete" && turn.result && turn.jobId ? <SearchFeedback jobId={turn.jobId} available={!!turn.feedback_available} /> : null}
        {turn.status === "running" && turn.findings_limited ? <AppText size={12} muted>سقف نمایش تدریجی پر شده است؛ بررسی ادامه یافته و نتیجهٔ نهایی جداگانه نمایش داده می‌شود.</AppText> : null}
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
      <Pressable testID="reference-send" accessibilityRole="button" onPress={() => void send()} disabled={recovering || !!active || creditBlocked || credits.isLoading || !status.data?.enabled || !state.draft.trim()}
        style={{ minHeight: 48, paddingHorizontal: 18, justifyContent: "center", borderRadius: 12, backgroundColor: colors.accent,
          opacity: recovering || active || creditBlocked || credits.isLoading || !status.data?.enabled || !state.draft.trim() ? 0.5 : 1 }}>
        <AppText weight="800" color={colors.onAccent}>{active ? "…" : "جست‌وجو"}</AppText>
      </Pressable>
    </View>
  </KeyboardAvoidingView>;
}
