import { useQuery } from "@tanstack/react-query";
import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, View } from "react-native";
import { TextInput } from "@/components/primitives/TextInput";
import Svg, { Path } from "react-native-svg";
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
import { ReferenceAnswerText } from "@/components/ReferenceAnswerText";
import { answerFollowOffset } from "@/utils/referenceAnswer";
import { referenceFailure as failure } from "@/utils/referenceFailure";
import { cancelReferenceTiming, noteReferenceRender, startReferenceTiming } from "@/api/referenceTiming";
import { pickClinicalSearchSuggestions } from "@/data/clinicalSearchSuggestions";
import { radius as radii, spacing } from "@/theme/tokens";

export function AiLabScreen() {
  const { colors } = useTheme();
  const { row, isFa } = useLang();
  const { navigate, goBack } = useNav();
  const userId = useAuth((s) => s.user?.id ?? null);
  const state = useAiLab();
  const clearance = useNavClearance();
  const scroll = useRef<ScrollView>(null);
  const followResults = useRef(true);
  const [followingAnswer, setFollowingAnswer] = useState(true);
  const turnPositions = useRef<Record<string, number>>({});
  const answerPositions = useRef<Record<string, number>>({});
  const answerHeights = useRef<Record<string, number>>({});
  const viewport = useRef({ height: 0, y: 0 });
  const followFrame = useRef<number | null>(null);
  const autoScrollUntil = useRef(0);
  const sending = useRef(false);
  const [requestError, setRequestError] = useState("");
  const [suggestions] = useState(() => pickClinicalSearchSuggestions());
  const questionInput = useRef<TextInput>(null);
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
  const latestRef = useRef(latest);
  latestRef.current = latest;
  const scheduleFollow = useCallback(() => {
    if (!followResults.current || followFrame.current !== null) return;
    followFrame.current = requestAnimationFrame(() => {
      followFrame.current = null;
      const turn = latestRef.current;
      if (!turn || !followResults.current || !viewport.current.height) return;
      const top = (turnPositions.current[turn.id] ?? 0) + (answerPositions.current[turn.id] ?? 0);
      const y = answerFollowOffset(top, answerHeights.current[turn.id] ?? 0, viewport.current.height);
      autoScrollUntil.current = Date.now() + 200;
      scroll.current?.scrollTo({ y, animated: false });
    });
  }, []);
  const pauseFollow = useCallback(() => {
    if (latestRef.current?.status !== "running") return;
    followResults.current = false;
    setFollowingAnswer(false);
  }, []);
  useEffect(() => () => { if (followFrame.current !== null) cancelAnimationFrame(followFrame.current); }, []);
  useEffect(() => {
    if (!latest) return;
    const previous = lastVisible.current;
    lastVisible.current = { id: latest.id };
    if (latest.status === "running" && previous.id !== latest.id) {
      followResults.current = true;
      setFollowingAnswer(true);
    }
    scheduleFollow();
  }, [latest?.id, latest?.status, latest?.answer_drafts, scheduleFollow]);
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
      answer_drafts: job.answer_drafts, cancellable: job.cancellable,
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
            else if (event.type === "progress") useAiLab.getState().patch(active.id, { stage: event.stage });
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
    <View style={{height:76}}><HeaderMesh><View style={{ paddingHorizontal:20,paddingTop:12,gap:8 }}>
      <View style={{flexDirection:row,alignItems:"center",gap:10}}>
        <ChromeButton onPress={goBack} size={44} accessibilityLabel={isFa ? "بازگشت" : "Back"}><AppText weight="800" size={18}>{isFa ? "›" : "‹"}</AppText></ChromeButton>
        <AppText accessibilityRole="header" aria-level={1} color="#FFFFFF" weight="800" size={17} style={{flex:1}}>{isFa ? "سرچ هوشمند" : "Smart search"}</AppText>
        <ThemeToggleButton variant="soft" size={44} /><LangToggleButton size={44} />
      </View>
    </View></HeaderMesh></View>
    <View style={{paddingHorizontal:20,paddingTop:12}}>
      <SmartSearchWallet compact refreshKey={`${latest?.jobId ?? ""}:${latest?.status ?? ""}`} running={!!active} />
    </View>
    <ScrollView ref={scroll} scrollEventThrottle={100}
      {...(Platform.OS === "web" ? { onWheel: pauseFollow } : {})}
      onScrollBeginDrag={pauseFollow}
      onLayout={({ nativeEvent }) => { viewport.current.height = nativeEvent.layout.height; scheduleFollow(); }}
      onScroll={({ nativeEvent }) => {
        const previousY = viewport.current.y;
        viewport.current.y = nativeEvent.contentOffset.y;
        if (Date.now() > autoScrollUntil.current && nativeEvent.contentOffset.y < previousY - 12) pauseFollow();
      }}
      onContentSizeChange={() => {
        if (latestRef.current?.status === "running") scheduleFollow();
      }} contentContainerStyle={{ padding: 20, gap: 18, flexGrow: 1 }}>
      {!turns.length ? <View style={{ gap: 20, paddingTop: 12 }}>
        <View style={{ gap: 8 }}>
          <AppText weight="800" size={23}>{isFa ? "پرسش شما، متن اصلی منبع" : "Your question, the original source"}</AppText>
          <AppText size={14} muted>{isFa ? "پرسش بالینی‌تان را بنویسید و پاسخ را کنار منبع بخوانید." : "Ask your clinical question and read the answer alongside its source."}</AppText>
        </View>
        <AppText size={12} muted>{isFa ? "پرسش‌های پیشنهادی" : "Suggested questions"}</AppText>
        <View style={{ backgroundColor: colors.cardBg, borderWidth: 1, borderColor: colors.border, borderRadius: radii.card, paddingHorizontal: spacing.lg }}>
        {suggestions.map((item, index) => <Pressable key={item.id} testID={`reference-suggestion-${item.id}`} accessibilityRole="button"
          accessibilityHint={isFa ? "فقط متن سؤال را وارد کادر می‌کند؛ برای ارسال، جست‌وجو را بزنید." : "Fills the question field. Press Search to submit."}
          onPress={() => { useAiLab.setState({ draft: isFa ? item.fa : item.en }); questionInput.current?.focus(); }}
          style={{ minHeight: 60, paddingVertical: 12, flexDirection: row, alignItems: "center", gap: 10,
            borderBottomWidth: index < suggestions.length - 1 ? 1 : 0, borderBottomColor: colors.border }}>
          <AppText size={13} style={{ flex: 1 }}>{isFa ? item.fa : item.en}</AppText>
          <Svg width={17} height={17} viewBox="0 0 24 24" fill="none" stroke={colors.muted} strokeWidth={1.7} accessibilityElementsHidden>
            <Path d={isFa ? "M20 12H4m6-6-6 6 6 6" : "M4 12h16m-6-6 6 6-6 6"} strokeLinecap="round" strokeLinejoin="round" />
          </Svg>
        </Pressable>)}
        </View>
        <AppText size={12} muted>{isFa ? "با انتخاب پیشنهاد، فقط کادر سؤال پر می‌شود." : "Selecting a suggestion only fills the question field."}</AppText>
      </View> : null}
      {status.isError ? <AppText size={13} muted>دریافت وضعیت سرچ هوشمند ممکن نشد. <AppText color={colors.accent} onPress={() => void status.refetch()}>تلاش دوباره</AppText></AppText> : null}
      {status.data && !status.data.enabled ? <AppText size={14} muted>سرچ هوشمند برای حساب شما فعال نیست.</AppText> : null}
      {turns.map((turn) => {
        const draft = Object.values(turn.answer_drafts ?? {}).join("\n\n");
        const hasFinalSources = !!turn.result?.parts.some((part) => part.items.length);
        const citations = turn.result?.parts.flatMap((part) => part.items)
          ?? (turn.status === "running" ? (turn.findings ?? []).map((finding) => finding.citation) : []);
        const articles = new Map<string, LabCitation>();
        for (const citation of citations) {
          const articleId = String(citation.target.params.id);
          if (!articles.has(articleId)) articles.set(articleId, citation);
        }
        const hasSources = articles.size > 0;
        return <View testID={turn.status === "complete" ? "reference-final-answer" : "reference-pending-answer"} key={turn.id} onLayout={(event) => { turnPositions.current[turn.id] = event.nativeEvent.layout.y; scheduleFollow(); }} style={{ gap: 12 }}>
        <View style={{backgroundColor:colors.accent,borderRadius:18,padding:14,maxWidth:"95%",alignSelf:isFa ? "flex-end" : "flex-start"}}><AppText color={colors.onAccent} size={14}>{turn.question}</AppText></View>
        {citations.some(c => c.media?.length) ? <View testID="reference-primary-media" style={{padding:16,borderRadius:18,backgroundColor:colors.cardBg}}>
          <ReferenceMediaCards items={[...new Map(citations.flatMap(c => c.media??[]).map(item => [item.article_id+":"+item.key,item])).values()]} />
        </View> : null}
        <View testID="reference-answer-summary" onLayout={(event) => {
          answerPositions.current[turn.id] = event.nativeEvent.layout.y;
          answerHeights.current[turn.id] = event.nativeEvent.layout.height;
          scheduleFollow();
        }}
          style={{ backgroundColor: colors.cardBg, borderWidth: 1, borderColor: colors.border, borderRadius: radii.card, padding: spacing.lg, gap: 14 }}>
          <AppText weight="800" size={14}>{isFa ? "پاسخ فارسی" : "Answer"}</AppText>
          {turn.status === "running" && !draft ? <ReferenceAnswerSkeleton /> : null}
          {turn.status === "running" && draft ? <View style={{ gap: 8 }}>
            <AppText muted size={12}>{isFa ? "پیش‌نویس در حال بررسی" : "Draft under review"}</AppText>
            <ReferenceAnswerText text={draft} testID="reference-answer-draft" />
          </View> : null}
          {turn.status === "failed" ? <AppText size={14} color={colors.denyLabel}>{failure(turn.error?.code, turn.error?.provider_status)}</AppText> : null}
          {turn.result?.parts.length === 0 ? <AppText size={14} muted>در محدودهٔ منابع انتخاب‌شده پاسخی پیدا نشد.</AppText> : null}
          {turn.result?.parts.map((part, i) => {
            const summary = part.overview_fa || [...new Set(part.items.map((item) => item.summary_fa))].join("\n\n");
            return <View key={i} style={{ gap: 10 }}>
              {turn.result!.parts.length > 1 ? <AppText weight="700" size={14}>{part.question_fa}</AppText> : null}
              {summary ? <ReferenceAnswerText testID="reference-answer-text" text={summary} /> : null}
              {part.retrieval?.limited && !part.retrieval.early_stopped ? <AppText size={12} muted>نمایش نتایج بازیابی‌شده در محدودهٔ این جست‌وجو؛ پوشش منابع کامل نیست.</AppText> : null}
              {part.status === "partial" ? <AppText size={13} muted>{part.clarification_fa || "این منابع فقط بخشی از سؤال را پوشش می‌دهند؛ پاسخ کامل تأیید نشد."}</AppText> : null}
              {part.status === "needs_clarification" ? <AppText size={14}>{part.clarification_fa}</AppText> : null}
              {part.status === "not_found" ? <AppText size={14} muted>متن کافی برای پاسخ مستند پیدا نشد؛ پاسخی حدس زده نشد.</AppText> : null}
            </View>;
          })}
          {turn.status === "running" ? <View style={{ gap: 8 }}>
            <ReferenceSearchLoading hasResults={hasSources} stage={turn.stage} />
            {turn.jobId && turn.cancellable ? <Pressable accessibilityRole="button" onPress={() => {
              void aiLabApi.cancel(turn.jobId!).catch(() => setRequestError("لغو درخواست انجام نشد؛ دوباره تلاش کنید."));
            }} style={{ minHeight: 44, justifyContent: "center" }}><AppText size={13} color={colors.denyLabel}>{isFa ? "توقف جست‌وجو" : "Stop search"}</AppText></Pressable> : null}
          </View> : null}
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
        {turn.status === "complete" && turn.result && turn.jobId ? <SearchFeedback jobId={turn.jobId} available={!!turn.feedback_available} /> : null}
        {turn.status === "running" && turn.findings_limited ? <AppText size={12} muted>سقف نمایش تدریجی پر شده است؛ بررسی ادامه یافته و نتیجهٔ نهایی جداگانه نمایش داده می‌شود.</AppText> : null}
        {turn.result?.warnings.length ? <AppText muted size={12}>برخی منابع یا توضیح‌ها قابل تأیید نبودند و کنار گذاشته شدند.</AppText> : null}
        {turn.status === "failed" ? <Pressable disabled={!!active} onPress={() => void send(turn.question)} style={{ minHeight: 44, justifyContent: "center" }}><AppText size={13} muted>تلاش دوباره</AppText></Pressable> : null}
      </View>; })}
    </ScrollView>
    {active && !followingAnswer ? <Pressable testID="reference-follow-answer" accessibilityRole="button"
      onPress={() => { followResults.current = true; setFollowingAnswer(true); scheduleFollow(); }}
      style={{ minHeight: 44, paddingHorizontal: 20, alignItems: "center", justifyContent: "center", backgroundColor: colors.cardBg }}>
      <AppText size={13} weight="700" color={colors.accent}>{isFa ? "دنبال‌کردن پاسخ" : "Follow the answer"}</AppText>
    </Pressable> : null}
    {requestError ? <AppText size={12} color={colors.denyLabel} style={{ paddingHorizontal: 20 }}>{requestError}</AppText> : null}
    {recovering ? <AppText size={12} muted style={{ paddingHorizontal: 20 }}>بررسی درخواست قبلی…</AppText> : null}
    <View style={{ paddingHorizontal: 16, paddingTop: 12, paddingBottom: 14, gap: 8, flexDirection: row, alignItems: "flex-end", backgroundColor: colors.cardBg, borderTopWidth: 1, borderTopColor: colors.border }}>
      <TextInput ref={questionInput} testID="reference-question" value={state.draft} onChangeText={(draft) => useAiLab.setState({ draft })} multiline maxLength={1500} editable={!active}
        accessibilityLabel="پرسش برای سرچ هوشمند" placeholder="سؤال خود را بنویسید…" placeholderTextColor={colors.muted}
        style={{ flex: 1, minHeight: 48, maxHeight: 120, padding: 12, borderRadius: radii.input, backgroundColor: colors.softBg, borderWidth: 1, borderColor: colors.border,
          fontFamily: fontFamily("500"), fontSize: 14, color: colors.ink, textAlign: isFa ? "right" : "left" }} />
      <Pressable testID="reference-send" accessibilityRole="button" onPress={() => void send()} disabled={recovering || !!active || creditBlocked || credits.isLoading || !status.data?.enabled || !state.draft.trim()}
        style={{ minHeight: 48, width: 48, alignItems: "center", justifyContent: "center", borderRadius: radii.btn, backgroundColor: colors.accent,
          opacity: recovering || active || creditBlocked || credits.isLoading || !status.data?.enabled || !state.draft.trim() ? 0.5 : 1 }}
        accessibilityLabel={isFa ? "جست‌وجو" : "Search"}>
        {active ? <AppText color={colors.onAccent}>…</AppText> : <Svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke={colors.onAccent} strokeWidth={1.7} accessibilityElementsHidden><Path d="m3 11 18-8-8 18-2-8-8-2zM11 13l10-10" strokeLinecap="round" strokeLinejoin="round" /></Svg>}
      </Pressable>
    </View>
  </KeyboardAvoidingView>;
}
