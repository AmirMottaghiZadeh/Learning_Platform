import { useQuery } from "@tanstack/react-query";
import * as Crypto from "expo-crypto";
import React, { useEffect, useRef, useState } from "react";
import { AppState, KeyboardAvoidingView, Platform, Pressable, ScrollView, TextInput, View } from "react-native";
import { supportApi, SupportMessage } from "@/api/support";
import { queryClient } from "@/api/queryClient";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { useNavClearance } from "@/components/BottomNav";
import { useAuth } from "@/store/auth";

/** The chat uses the same surfaces, typography and primary action as Settings. */
export function SupportScreen() {
  const { isFa, row } = useLang();
  const { colors } = useTheme();
  const clearance = useNavClearance();
  const goBack = useNav(s => s.goBack);
  const threadParam = useNav(s => s.params.conversationId) as string | undefined;
  const userId = useAuth(s => s.user?.id);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [older, setOlder] = useState<SupportMessage[]>([]);
  const [hasOlder, setHasOlder] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const scroll = useRef<ScrollView>(null);
  const nearBottom = useRef(true);
  const pending = useRef<{ text: string; id: string } | null>(null);
  const alive = useRef(true);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  const conversation = useQuery({ queryKey: ["support-conversation", userId, threadParam], queryFn: async () => {
    if (threadParam) {
      const threads = await supportApi.conversations();
      const found = threads.find(t => t.id === threadParam);
      if (found) return found;
    }
    return supportApi.create();
  }, staleTime: Infinity, retry: false });
  const thread = conversation.data;
  const latest = useQuery({ queryKey: ["support-messages", userId, thread?.id], queryFn: () => supportApi.messages(thread!.id), enabled: !!thread, refetchInterval: 3000, retry: false });
  const messages = [...new Map([...older, ...(latest.data?.messages ?? [])].map(m => [m.id, m])).values()].sort((a, b) => a.id - b.id);
  const last = latest.data?.messages.at(-1)?.id ?? 0;
  useEffect(() => {
    if (!thread || !last) return;
    if (Platform.OS === "web" ? document.hidden : AppState.currentState !== "active") return;
    void supportApi.read(thread.id, last).then(() => queryClient.invalidateQueries({ queryKey: ["support-summary"] })).catch(() => undefined);
  }, [thread?.id, last]);
  useEffect(() => { setOlder([]); setHasOlder(false); }, [thread?.id]);
  useEffect(() => { if (latest.data && !older.length) setHasOlder(latest.data.has_older); }, [latest.data]);
  useEffect(() => {
    if (!latest.data) return;
    setOlder(current => [...new Map([...current, ...latest.data.messages].map(message => [message.id, message])).values()]);
  }, [latest.data]);

  const send = async () => {
    if (!thread || sending || !text.trim()) return;
    const draft = text.trim();
    if (!pending.current || pending.current.text !== draft) pending.current = { text: draft, id: Crypto.randomUUID() };
    setSending(true); setError("");
    try {
      const sent = await supportApi.send(thread.id, draft, pending.current.id);
      if (!alive.current || useAuth.getState().user?.id !== userId) return;
      setOlder(current => [...current, sent]); setText(current => current.trim() === draft ? "" : current); pending.current = null;
      nearBottom.current = true;
      await latest.refetch();
    } catch { if (alive.current) setError(isFa ? "پیام ارسال نشد؛ متن حفظ شده است. دوباره ارسال کنید." : "Message not sent. Your text is saved; try again."); }
    finally { if (alive.current) setSending(false); }
  };
  const loadOlder = async () => {
    if (!thread || !messages.length || loadingOlder) return;
    setLoadingOlder(true);
    try {
      const page = await supportApi.messages(thread.id, { before: messages[0].id });
      setOlder(current => [...page.messages, ...current]); setHasOlder(page.has_older);
    } catch { setError(isFa ? "پیام‌های قبلی دریافت نشدند." : "Could not load earlier messages."); }
    finally { setLoadingOlder(false); }
  };

  return <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={{ flex: 1, backgroundColor: colors.appBg, paddingBottom: clearance }}>
    <View style={{ paddingHorizontal: 20, paddingTop: 12, backgroundColor: colors.cardBg }}><ScreenChrome title={isFa ? "پشتیبانی" : "Support"} onBack={goBack} /><AppText muted size={12} style={{ marginBottom: 12 }}>{isFa ? "تیم فارمنتا · پیام‌هایتان اینجا محفوظ می‌ماند." : "Pharmenta team · Your conversation stays here."}</AppText></View>
    {conversation.isPending || (!!thread && latest.isPending) ? <LoadingState /> : conversation.isError || latest.isError && !latest.data ? <View style={{ flex: 1, padding: 24, justifyContent: "center", gap: 12 }}><AppText muted>{isFa ? "دریافت گفت‌وگو انجام نشد. اتصال را بررسی کنید." : "Could not load your conversation. Check your connection."}</AppText><Pressable onPress={() => { void conversation.refetch(); void latest.refetch(); }} style={{ minHeight: 44, justifyContent: "center" }}><AppText color={colors.accent}>{isFa ? "تلاش دوباره" : "Try again"}</AppText></Pressable></View> : <ScrollView ref={scroll} onScroll={e => { const n = e.nativeEvent; nearBottom.current = n.contentSize.height - n.contentOffset.y - n.layoutMeasurement.height < 120; }} scrollEventThrottle={64} onContentSizeChange={() => { if (nearBottom.current) scroll.current?.scrollToEnd({ animated: true }); }} contentContainerStyle={{ padding: 18, gap: 16, flexGrow: 1 }}>
      {hasOlder ? <Pressable onPress={loadOlder} disabled={loadingOlder} style={{ alignSelf: "center", minHeight: 44, justifyContent: "center" }}><AppText size={12} muted>{loadingOlder ? "…" : isFa ? "پیام‌های قدیمی‌تر" : "Earlier messages"}</AppText></Pressable> : null}
      {!messages.length ? <View style={{ paddingVertical: 32, gap: 8 }}><AppText weight="800" size={18}>{isFa ? "چطور می‌توانیم کمک کنیم؟" : "How can we help?"}</AppText><AppText muted size={13}>{isFa ? "سؤالتان دربارهٔ اپ، اشتراک یا دانلودها را برای تیم پشتیبانی بنویسید." : "Ask our team about the app, your subscription or downloads."}</AppText></View> : null}
      {messages.map(message => <View key={message.id} style={{ alignSelf: message.from_staff ? (isFa ? "flex-end" : "flex-start") : (isFa ? "flex-start" : "flex-end"), maxWidth: "92%", backgroundColor: message.from_staff ? colors.cardBg : colors.accent, padding: 14, borderRadius: 18, borderBottomRightRadius: message.from_staff ? 18 : 4, borderBottomLeftRadius: message.from_staff ? 4 : 18, borderWidth: message.from_staff ? 1 : 0, borderColor: colors.trackBg }}><AppText size={14} color={message.from_staff ? colors.ink : colors.onAccent} style={{ lineHeight: 24 }}>{message.text}</AppText><AppText size={11} color={message.from_staff ? colors.muted : colors.onAccentSub} style={{ marginTop: 6 }}>{message.from_staff ? (isFa ? "پشتیبانی فارمنتا · " : "Pharmenta support · ") : ""}{new Date(message.created_at).toLocaleString(isFa ? "fa-IR" : "en", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}{!message.from_staff && (latest.data?.staff_read_id ?? 0) >= message.id ? (isFa ? " · دیده شد" : " · Read") : ""}</AppText></View>)}
    </ScrollView>}
    {error || latest.isError && latest.data ? <AppText size={12} color={colors.denyLabel} style={{ paddingHorizontal: 18, paddingVertical: 8 }}>{error || (isFa ? "اتصال قطع است؛ برای پیام تازه دوباره تلاش می‌شود." : "Disconnected. Retrying for new messages.")}</AppText> : null}
    <View style={{ flexDirection: row, alignItems: "flex-end", gap: 10, padding: 12, backgroundColor: colors.cardBg, borderTopWidth: 1, borderTopColor: colors.sheetLine }}><TextInput accessibilityLabel={isFa ? "پیام شما" : "Your message"} placeholder={isFa ? "پیامتان را بنویسید…" : "Write a message…"} placeholderTextColor={colors.muted} value={text} onChangeText={setText} multiline maxLength={4000} style={{ flex: 1, minHeight: 48, maxHeight: 140, padding: 12, backgroundColor: colors.softBg, borderRadius: 14, fontFamily: fontFamily("500"), fontSize: 14, textAlign: isFa ? "right" : "left", color: colors.ink }} /><Pressable onPress={() => void send()} disabled={!thread || sending || !text.trim()} accessibilityRole="button" style={{ minHeight: 48, paddingHorizontal: 18, justifyContent: "center", borderRadius: 14, backgroundColor: colors.accent, opacity: !thread || sending || !text.trim() ? 0.6 : 1 }}><AppText weight="800" color={colors.onAccent}>{sending ? "…" : isFa ? "ارسال" : "Send"}</AppText></Pressable></View>
  </KeyboardAvoidingView>;
}
