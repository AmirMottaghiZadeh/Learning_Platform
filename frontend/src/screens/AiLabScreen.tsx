import { useQuery } from "@tanstack/react-query";
import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, View } from "react-native";
import { TextInput } from "@/components/primitives/TextInput";
import Svg, { Path } from "react-native-svg";
import { aiLabApi, LAB_MODEL, LabCitation, LabHistoryEntry } from "@/api/aiLab";
import { ApiError } from "@/api/client";
import { searchWalletApi } from "@/api/searchWallet";
import { ChromeButton, LangToggleButton } from "@/components/ScreenChrome";
import { ThemeToggleButton } from "@/components/ThemeToggleButton";
import { AppText } from "@/components/primitives/AppText";
import { useNavClearance } from "@/components/BottomNav";
import { LabTurn, useAiLab } from "@/store/aiLab";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { useLang } from "@/i18n/LanguageProvider";
import { fontFamily } from "@/theme/fonts";
import { SearchFeedback } from "@/components/SearchFeedback";
import { SmartSearchWallet } from "@/components/SmartSearchWallet";
import { ReferenceMediaCards } from "@/components/ReferenceMediaCards";
import { referenceMediaId } from "@/api/referenceMedia";
import { Chevron } from "@/components/primitives/Chevron";
import { ReferenceAnswerSkeleton, ReferenceSearchLoading } from "@/components/ReferenceSearchLoading";
import { ReferenceAnswerText } from "@/components/ReferenceAnswerText";
import { SmartSearchHistory } from "@/components/SmartSearchHistory";
import { useBackInterceptor } from "@/navigation/back";
import { answerFollowOffset } from "@/utils/referenceAnswer";
import { referenceFailure as failure } from "@/utils/referenceFailure";
import { cancelReferenceTiming, noteReferenceRender, startReferenceTiming } from "@/api/referenceTiming";
import { pickClinicalSearchSuggestions } from "@/data/clinicalSearchSuggestions";
import { radius as radii, spacing } from "@/theme/tokens";

export function AiLabScreen() {
  const { colors } = useTheme();
  const { row, isFa, t } = useLang();
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
  const [cancellingJob, setCancellingJob] = useState<string | null>(null);
  const [suggestions] = useState(() => pickClinicalSearchSuggestions());
  const questionInput = useRef<TextInput>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyOpening, setHistoryOpening] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState(false);
  const historyRequest = useRef(0);
  const lastVisible = useRef({ id: "" });
  const [recovering, setRecovering] = useState(true);
  const status = useQuery({ queryKey: ["ai-lab-status", userId], queryFn: aiLabApi.status, retry: false, staleTime: 0 });
  const credits=useQuery({queryKey:["ai-search-wallet",userId],queryFn:searchWalletApi.summary,enabled:userId!==null,retry:false,staleTime:10000});
  const creditBlocked=credits.data?.can_search===false;
  const turns = state.owner === userId ? state.turns : [];
  const archivedTurn = state.owner === userId ? state.archivedTurn : null;
  const displayedTurns = archivedTurn ? [archivedTurn] : turns;
  const active = turns.find((t) => t.status === "running");
  const latest = turns[turns.length - 1];
  const latestRef = useRef(latest);
  latestRef.current = latest;
  const scheduleFollow = useCallback(() => {
    if (!followResults.current || followFrame.current !== null) return;
    followFrame.current = requestAnimationFrame(() => {
      followFrame.current = null;
      const turn = latestRef.current;
      if (!turn || useAiLab.getState().archivedTurn || !followResults.current || !viewport.current.height) return;
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
    if(creditBlocked){setRequestError(failure("AI_CREDIT_INSUFFICIENT", undefined, isFa));return;}
    sending.current = true; setRequestError("");
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    startReferenceTiming(id);
    const history = turns.filter((t) => t.question !== q).slice(-4).map((t) => t.question);
    useAiLab.setState((s) => ({ turns: [...s.turns, { id, question: q, model: LAB_MODEL, status: "running", stage: "starting" }], draft: "", archivedTurn: null }));
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
            setRequestError(isFa ? "جست‌وجوی قبلی بازیابی شد؛ نتیجه در همین گفت‌وگو نمایش داده می‌شود." : "The previous search was recovered and will appear here.");
            return;
          }
        } catch { /* Keep the submitted question available for retry. */ }
      }
      if (useAiLab.getState().owner === userId) useAiLab.getState().patch(id, { status: "failed", error: { code: error instanceof ApiError ? error.code : "REQUEST_FAILED" } });
      setRequestError(error instanceof ApiError && [402, 429].includes(error.status) ? failure(error.code, error.status, isFa)
        : isFa ? "ارسال سؤال انجام نشد؛ سؤال در گفت‌وگو باقی مانده است." : "Could not submit the question. You can retry it here.");
    } finally { sending.current = false; }
  };

  const stopSearch = async () => {
    if (!active?.jobId || cancellingJob) return;
    setCancellingJob(active.jobId);
    try {
      await aiLabApi.cancel(active.jobId);
    } catch {
      setCancellingJob(null);
      setRequestError(isFa ? "توقف جست‌وجو انجام نشد؛ دوباره تلاش کنید." : "Could not stop the search. Try again.");
    }
  };
  useEffect(() => {
    if (!active) setCancellingJob(null);
  }, [active?.id]);

  const open = (citation: LabCitation) => {
    const { screen, params } = citation.target;
    if (screen === "uptodateArticle") navigate("uptodateArticle", params);
  };

  const closeHistory = () => {
    historyRequest.current += 1;
    setHistoryOpen(false);
    setHistoryOpening(null);
    setHistoryError(false);
  };
  const closeArchive = () => {
    useAiLab.setState({ archivedTurn: null });
    followResults.current = true;
    setFollowingAnswer(true);
    scheduleFollow();
  };
  useBackInterceptor(historyOpen || !!archivedTurn, historyOpen ? closeHistory : closeArchive);

  const openHistoryEntry = async (entry: LabHistoryEntry) => {
    if (userId === null || historyOpening) return;
    const attempt = ++historyRequest.current;
    setHistoryError(false);
    setHistoryOpening(entry.job_id);
    try {
      const job = await aiLabApi.result(entry.job_id);
      if (historyRequest.current !== attempt || useAuth.getState().user?.id !== userId) return;
      useAiLab.setState({ archivedTurn: { ...job, id: `archive:${entry.job_id}`, jobId: entry.job_id, model: LAB_MODEL, question: entry.question } });
      followResults.current = false;
      setFollowingAnswer(false);
      scroll.current?.scrollTo({ y: 0, animated: false });
      closeHistory();
    } catch {
      if (historyRequest.current === attempt && useAuth.getState().user?.id === userId) setHistoryError(true);
    } finally {
      if (historyRequest.current === attempt) setHistoryOpening(null);
    }
  };

  const sectionName = (citation: LabCitation) => citation.section_path?.join(" › ") || citation.section;
  const sourceLink = (citation: LabCitation, number: number) => (
    <Pressable key={citation.source_id} testID="reference-inline-citation" accessibilityRole="link" onPress={() => open(citation)}
      hitSlop={{ top: 6, bottom: 6, left: 0, right: 0 }}
      accessibilityLabel={`${isFa ? "منبع" : "Source"} ${number} · ${citation.title}${sectionName(citation) ? ` · ${sectionName(citation)}` : ""}`}
      style={({ pressed }) => ({ minHeight: 32, minWidth: 44, alignItems: "center", justifyContent: "center",
        borderRadius: 8, backgroundColor: colors.softBg, opacity: pressed ? 0.72 : 1 })}>
      <AppText size={12} color={colors.accent} weight="700" style={{ writingDirection: "ltr" }}>
        [{number}]
      </AppText>
    </Pressable>
  );

  return <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={{ flex: 1, backgroundColor: colors.appBg, paddingBottom: clearance }}>
    {historyOpen ? <SmartSearchHistory userId={userId} visible opening={historyOpening} openError={historyError}
      onClose={closeHistory} onOpen={(entry) => void openHistoryEntry(entry)} /> : null}
    <View style={{ backgroundColor: colors.cardBg, borderBottomWidth: 1, borderBottomColor: colors.border }}>
      <View style={{ paddingHorizontal: spacing.lg, paddingVertical: spacing.sm, flexDirection: row, alignItems: "center", gap: spacing.sm }}>
        <ChromeButton onPress={archivedTurn ? closeArchive : goBack} accessibilityLabel={isFa ? "بازگشت" : "Back"}><Chevron back color={colors.ink} /></ChromeButton>
        <AppText accessibilityRole="header" aria-level={1} weight="700" size={17} style={{ flex: 1 }}>{t("resourceLookupSmart")}</AppText>
        <ThemeToggleButton variant="soft" /><LangToggleButton />
      </View>
      <View style={{ paddingHorizontal: spacing.lg }}>
        <SmartSearchWallet compact refreshKey={`${latest?.jobId ?? ""}:${latest?.status ?? ""}`} running={!!active} />
        <Pressable testID="smart-search-history-open" accessibilityRole="button" onPress={() => setHistoryOpen(true)}
          style={{ minHeight: 44, flexDirection: row, alignItems: "center", alignSelf: isFa ? "flex-end" : "flex-start", gap: spacing.sm }}>
          <Svg width={17} height={17} viewBox="0 0 24 24" fill="none" stroke={colors.accent} strokeWidth={1.7} aria-hidden>
            <Path d="M3 12a9 9 0 1 1 2.6 6.4M3 12V6m0 6h6m3-5v5l3 2" strokeLinecap="round" strokeLinejoin="round" />
          </Svg>
          <AppText size={13} color={colors.accent} weight="700">{isFa ? "تاریخچهٔ جست‌وجو" : "Search history"}</AppText>
        </Pressable>
      </View>
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
      }} contentContainerStyle={{ width: "100%", maxWidth: 780, alignSelf: "center", padding: spacing.lg, gap: spacing.lg, flexGrow: 1 }}>
      {!displayedTurns.length ? <View style={{ gap: spacing.md, paddingTop: spacing.sm }}>
        <View style={{ gap: 8 }}>
          <AppText weight="700" size={22}>{isFa ? "پرسش شما، متن اصلی منبع" : "Your question, the original source"}</AppText>
          <AppText size={14} muted>{isFa ? "پرسش بالینی‌تان را بنویسید و پاسخ را کنار منبع بخوانید." : "Ask your clinical question and read the answer alongside its source."}</AppText>
        </View>
        <AppText size={13} muted>{isFa ? "پرسش‌های پیشنهادی" : "Suggested questions"}</AppText>
        <View style={{ backgroundColor: colors.cardBg, boxShadow: colors.cardShadow, borderRadius: radii.card, paddingHorizontal: spacing.lg }}>
        {suggestions.map((item, index) => <Pressable key={item.id} testID={`reference-suggestion-${item.id}`} accessibilityRole="button"
          accessibilityHint={isFa ? "فقط متن سؤال را وارد کادر می‌کند؛ برای ارسال، جست‌وجو را بزنید." : "Fills the question field. Press Search to submit."}
          onPress={() => { useAiLab.setState({ draft: isFa ? item.fa : item.en }); questionInput.current?.focus(); }}
          style={{ minHeight: 52, paddingVertical: 8, flexDirection: row, alignItems: "center", gap: 10,
            borderBottomWidth: index < suggestions.length - 1 ? 1 : 0, borderBottomColor: colors.border }}>
          <AppText size={14} style={{ flex: 1 }}>{isFa ? item.fa : item.en}</AppText>
          <Svg width={17} height={17} viewBox="0 0 24 24" fill="none" stroke={colors.muted} strokeWidth={1.7} accessibilityElementsHidden>
            <Path d={isFa ? "M20 12H4m6-6-6 6 6 6" : "M4 12h16m-6-6 6 6-6 6"} strokeLinecap="round" strokeLinejoin="round" />
          </Svg>
        </Pressable>)}
        </View>
        <AppText size={12} muted>{isFa ? "با انتخاب پیشنهاد، فقط کادر سؤال پر می‌شود." : "Selecting a suggestion only fills the question field."}</AppText>
      </View> : null}
      {status.isError ? <AppText size={13} muted>{isFa ? "دریافت وضعیت سرچ هوشمند ممکن نشد. " : "Could not check search availability. "}<AppText color={colors.accent} onPress={() => void status.refetch()}>{isFa ? "تلاش دوباره" : "Retry"}</AppText></AppText> : null}
      {status.data && !status.data.enabled ? <AppText size={14} muted>{failure("AI_LAB_DISABLED", undefined, isFa)}</AppText> : null}
      {displayedTurns.map((turn) => {
        const draft = Object.values(turn.answer_drafts ?? {}).join("\n\n");
        const citations = turn.result?.parts.flatMap((part) => [...part.items, ...(part.related_items ?? []).filter((item) => item.media?.length)])
          ?? (turn.status === "running" ? (turn.findings ?? []).map((finding) => finding.citation) : []);
        const articles = new Map<string, LabCitation>();
        for (const citation of citations) {
          const articleId = String(citation.target.params.id);
          if (!articles.has(articleId)) articles.set(articleId, citation);
        }
        const hasSources = articles.size > 0;
        const mediaSources = new Map<string, { item: NonNullable<LabCitation["media"]>[number]; citation: LabCitation }>();
        for (const citation of citations) {
          for (const item of citation.media ?? []) {
            const id = referenceMediaId(item);
            if (!mediaSources.has(id)) mediaSources.set(id, { item, citation });
          }
        }
        return <View testID={turn.status === "complete" ? "reference-final-answer" : "reference-pending-answer"} key={turn.id} onLayout={(event) => { turnPositions.current[turn.id] = event.nativeEvent.layout.y; scheduleFollow(); }} style={{ gap: 12 }}>
        <View style={{backgroundColor:colors.leitnerActiveBg,borderRadius:14,padding:12,maxWidth:"92%",alignSelf:isFa ? "flex-end" : "flex-start"}}><AppText color={colors.ink} weight="500" size={15}>{turn.question}</AppText></View>
        {mediaSources.size ? <View testID="reference-primary-media" style={{padding:16,borderRadius:18,backgroundColor:colors.cardBg}}>
          <ReferenceMediaCards items={[...mediaSources.values()].map(({ item }) => item)} onOpenSource={(item) => {
            const source = mediaSources.get(referenceMediaId(item));
            if (source) open(source.citation);
          }} />
        </View> : null}
        <View testID="reference-answer-summary" onLayout={(event) => {
          answerPositions.current[turn.id] = event.nativeEvent.layout.y;
          answerHeights.current[turn.id] = event.nativeEvent.layout.height;
          scheduleFollow();
        }}
          style={{ backgroundColor: colors.cardBg, boxShadow: colors.cardShadow, borderRadius: radii.card, padding: spacing.lg, gap: 14 }}>
          <AppText weight="700" size={15}>{isFa ? "پاسخ فارسی" : "Answer in Persian"}</AppText>
          {turn.status === "running" && !draft ? <ReferenceAnswerSkeleton /> : null}
          {turn.status === "running" && draft ? <View style={{ gap: 6 }}>
            <AppText size={12} muted>{isFa ? "پیش‌نویس در حال بررسی" : "Draft under review"}</AppText>
            <ReferenceAnswerText text={draft} testID="reference-answer-draft" />
          </View> : null}
          {turn.status === "failed" ? <AppText size={14} color={colors.denyLabel}>{failure(turn.error?.code, turn.error?.provider_status, isFa)}</AppText> : null}
          {turn.result?.parts.length === 0 ? <AppText size={14} muted>{isFa ? "در محدودهٔ منابع انتخاب‌شده پاسخی پیدا نشد." : "No answer was found in the selected references."}</AppText> : null}
          {turn.result?.parts.map((part, i) => {
            const summary = part.overview_fa || [...new Set(part.items.map((item) => item.summary_fa))].join("\n\n");
            return <View key={i} style={{ gap: 10 }}>
              {turn.result!.parts.length > 1 ? <AppText weight="700" size={14}>{part.question_fa}</AppText> : null}
              {part.answer_blocks?.length ? <View testID="reference-answer-text" style={{ gap: 12 }}>
                {part.answer_blocks.map((block, index) => <View key={index} style={{ gap: 4 }}>
                  <ReferenceAnswerText text={block.text_fa} />
                  <View style={{ flexDirection: row, flexWrap: "wrap", gap: 4 }}>
                    {[...new Set(block.source_ids)].map((sourceId) => {
                      const position = part.items.findIndex(({ source_id }) => source_id === sourceId);
                      return position < 0 ? null : sourceLink(part.items[position], position + 1);
                    })}
                  </View>
                </View>)}
              </View> : summary ? <View style={{ gap: 4 }}>
                <ReferenceAnswerText testID="reference-answer-text" text={summary} />
                <View style={{ flexDirection: row, flexWrap: "wrap", gap: 4 }}>
                  {part.items.map((item, index) => sourceLink(item, index + 1))}
                </View>
              </View> : null}
              {part.retrieval?.limited && !part.retrieval.early_stopped ? <AppText size={12} muted>{isFa ? "پوشش منابع در این جست‌وجو کامل نیست." : "This search covered a limited set of references."}</AppText> : null}
              {part.status === "partial" ? <AppText size={13} muted>{part.clarification_fa || (isFa ? "منابع فقط بخشی از سؤال را پوشش می‌دهند." : "The sources cover only part of the question.")}</AppText> : null}
              {part.status === "needs_clarification" ? <AppText size={14}>{part.clarification_fa}</AppText> : null}
              {part.status === "not_found" ? <AppText size={14} muted>{isFa ? "متن کافی برای پاسخ مستند پیدا نشد." : "There was insufficient evidence for a sourced answer."}</AppText> : null}
            </View>;
          })}
        </View>
        {hasSources ? <View testID="reference-source-results" style={{ gap: 12 }}>
          <AppText weight="800" size={13}>{isFa ? turn.status === "running" ? "منابع در حال بررسی" : "منابع اصلی" : turn.status === "running" ? "Sources under review" : "Sources"}</AppText>
          <View style={{ borderRadius: radii.card, backgroundColor: colors.cardBg }}>
            {[...articles.values()].map((citation, index) => (
              <Pressable key={String(citation.target.params.id)} testID="reference-source" accessibilityRole="button" onPress={() => open(citation)}
                style={({ pressed }) => ({
                  flexDirection: row, alignItems: "center", gap: 12, minHeight: 60, padding: spacing.md,
                  borderTopWidth: index ? 1 : 0, borderTopColor: colors.border, opacity: pressed ? 0.75 : 1,
                })}>
                <View style={{ flex: 1, gap: 3 }}>
                  <AppText size={13} color={colors.accent} style={{ writingDirection: "ltr", textAlign: "left" }}>
                    {citation.section ? `UpToDate · ${citation.section}` : "UpToDate"}
                  </AppText>
                  <AppText weight="700" size={14} style={{ writingDirection: "ltr", textAlign: "left" }}>{citation.title}</AppText>
                </View>
                <Chevron />
              </Pressable>
            ))}
          </View>
        </View> : null}
        {turn.status === "complete" && turn.result && turn.jobId ? <SearchFeedback jobId={turn.jobId} available={!!turn.feedback_available} /> : null}
        {turn.status === "running" && turn.findings_limited ? <AppText size={12} muted>{isFa ? "بررسی منابع ادامه دارد. نتیجهٔ نهایی پس از تکمیل جست‌وجو نمایش داده می‌شود." : "Review is continuing. Final results will appear when the search is complete."}</AppText> : null}
        {turn.result?.warnings.length ? <AppText muted size={12}>{isFa ? "برخی منابع یا توضیح‌ها قابل تأیید نبودند." : "Some passages or explanations could not be verified."}</AppText> : null}
        {turn.status === "failed" ? <Pressable disabled={!!active} onPress={() => void send(turn.question)} style={{ minHeight: 44, justifyContent: "center" }}><AppText size={13} muted>{isFa ? "تلاش دوباره" : "Retry"}</AppText></Pressable> : null}
      </View>; })}
    </ScrollView>
    {active && !archivedTurn && !followingAnswer ? <Pressable testID="reference-follow-answer" accessibilityRole="button"
      onPress={() => { followResults.current = true; setFollowingAnswer(true); scheduleFollow(); }}
      style={{ minHeight: 44, paddingHorizontal: 20, alignItems: "center", justifyContent: "center", backgroundColor: colors.cardBg }}>
      <AppText size={13} weight="700" color={colors.accent}>{isFa ? "دنبال‌کردن پاسخ" : "Follow the answer"}</AppText>
    </Pressable> : null}
    {requestError ? <AppText size={12} color={colors.denyLabel} style={{ paddingHorizontal: 20 }}>{requestError}</AppText> : null}
    {recovering ? <AppText size={13} muted style={{ paddingHorizontal: 16 }}>{isFa ? "بررسی درخواست قبلی…" : "Recovering the previous search…"}</AppText> : null}
    {active ? <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between", gap: spacing.sm,
      paddingHorizontal: spacing.lg, backgroundColor: colors.cardBg, borderTopWidth: 1, borderTopColor: colors.border }}>
      <View style={{ flex: 1 }}><ReferenceSearchLoading hasResults={!!active.findings?.length} stage={active.stage} /></View>
      {active.jobId && active.cancellable ? <Pressable accessibilityRole="button" disabled={!!cancellingJob}
        onPress={() => void stopSearch()} style={{ minHeight: 44, paddingHorizontal: 4, justifyContent: "center" }}>
        <AppText size={13} color={colors.denyLabel}>{cancellingJob ? (isFa ? "در حال توقف…" : "Stopping…") : (isFa ? "توقف جست‌وجو" : "Stop search")}</AppText>
      </Pressable> : null}
    </View> : null}
    <View style={{ paddingHorizontal: 16, paddingVertical: 8, gap: 8, flexDirection: row, alignItems: "flex-end", backgroundColor: colors.cardBg, borderTopWidth: 1, borderTopColor: colors.border }}>
      <TextInput ref={questionInput} testID="reference-question" value={state.draft} onChangeText={(draft) => useAiLab.setState({ draft })} multiline maxLength={1500} editable={!active}
        accessibilityLabel={isFa ? "پرسش برای سرچ هوشمند" : "Question for smart search"} placeholder={isFa ? "سؤال خود را بنویسید…" : "Write your question…"} placeholderTextColor={colors.muted}
        style={{ flex: 1, minHeight: 48, maxHeight: 120, padding: 12, borderRadius: radii.input, backgroundColor: colors.softBg,
          fontFamily: fontFamily("500"), fontSize: 14, color: colors.ink, textAlign: isFa ? "right" : "left" }} />
      <Pressable testID="reference-send" accessibilityRole="button" onPress={() => void send()} disabled={recovering || !!active || creditBlocked || credits.isLoading || !status.data?.enabled || !state.draft.trim()}
        style={{ minHeight: 48, width: 48, alignItems: "center", justifyContent: "center", borderRadius: radii.btn, backgroundColor: colors.accent,
          opacity: recovering || active || creditBlocked || credits.isLoading || !status.data?.enabled || !state.draft.trim() ? 0.5 : 1 }}
        accessibilityLabel={isFa ? "جست‌وجو" : "Search"}>
        {active ? <AppText color={colors.onAccent}>…</AppText> : <Svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke={colors.onAccent} strokeWidth={1.7} accessibilityElementsHidden><Path d={isFa ? "m21 11-18-8 8 18 2-8 8-2zM13 13 3 3" : "m3 11 18-8-8 18-2-8-8-2zM11 13l10-10"} strokeLinecap="round" strokeLinejoin="round" /></Svg>}
      </Pressable>
    </View>
  </KeyboardAvoidingView>;
}
