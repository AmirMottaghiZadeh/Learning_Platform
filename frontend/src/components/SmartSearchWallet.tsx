import React, { useEffect, useRef, useState } from "react";
import { AppState, Linking, Modal, Platform, Pressable, ScrollView, View } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { searchWalletApi, SearchCreditPackage } from "@/api/searchWallet";
import { useAuth } from "@/store/auth";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { radius, spacing } from "@/theme/tokens";

function amount(value: string | number | undefined, fa: boolean) {
  if (value === undefined) return "—";
  const number=Number(value);
  if(!Number.isFinite(number))return "—";
  const whole=String(Math.sign(number)*Math.ceil(Math.abs(number)));
  const text = whole.replace(/\B(?=(\d{3})+(?!\d))/g, fa ? "٬" : ",");
  return fa ? text.replace(/\d/g, d => "۰۱۲۳۴۵۶۷۸۹"[Number(d)]) : text;
}

export function SmartSearchWallet({ refreshKey, running, compact=false }: { refreshKey: string; running: boolean; compact?: boolean }) {
  const { colors } = useTheme();
  const { isFa, row } = useLang();
  const owner = useAuth(s => s.user?.id ?? null);
  const [open, setOpen] = useState(false);
  const [paying, setPaying] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [gateway, setGateway] = useState("");
  const [paymentLink, setPaymentLink] = useState("");
  const [offset, setOffset] = useState(0);
  const [selectedPackage, setSelectedPackage] = useState<number | null>(null);
  const requestIds = useRef<Record<string, { id: string; price: number }>>({});
  const mounted = useRef(true);
  const account = useRef(owner);
  account.current = owner;
  const wallet = useQuery({ queryKey: ["ai-search-wallet", owner], queryFn: searchWalletApi.summary,
    enabled: owner !== null, staleTime: 10000, retry: false, refetchOnWindowFocus: true,
    refetchInterval: running ? 10000 : false });
  const history = useQuery({ queryKey: ["ai-search-wallet-history", owner, offset], queryFn: () => searchWalletApi.history(offset),
    enabled: open && owner !== null, staleTime: 0, retry: false, refetchOnWindowFocus: true });
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    setOpen(false); setPaying(null); setError(""); setPaymentLink(""); setOffset(0); setSelectedPackage(null); requestIds.current = {};
  }, [owner]);
  useEffect(() => { void wallet.refetch(); if (open) void history.refetch(); }, [refreshKey]);
  useEffect(() => {
    const subscription = AppState.addEventListener("change", state => {
      if (state === "active") { void wallet.refetch(); if (open) void history.refetch(); }
    });
    return () => subscription.remove();
  }, [open, owner]);
  const data = wallet.data;
  const exhausted=!!data?.billing_enabled && Number(data.balance)<=0;
  const low=!!data?.billing_enabled && Number(data.balance)>0 && Number(data.balance)<=10;
  const selectedGateway = data?.gateways.some(g => g.kind === gateway) ? gateway : data?.gateways[0]?.kind ?? "";
  const packageToBuy = data?.packages.find(pack => pack.id === selectedPackage) ?? data?.packages[0];
  useEffect(() => {
    const completed = new Set(data?.completed_topups ?? []);
    for (const [key, request] of Object.entries(requestIds.current)) if (completed.has(request.id)) delete requestIds.current[key];
  }, [data?.completed_topups]);
  const refresh = () => { void wallet.refetch(); void history.refetch(); };
  const pay = async (pack: SearchCreditPackage) => {
    if (paying !== null || !data?.topups_enabled) return;
    const expectedOwner = owner;
    const popup = Platform.OS === "web" ? window.open("about:blank", "_blank") : null;
    if (popup) popup.opener = null;
    const key = `${pack.id}:${selectedGateway}`;
    const purchase = requestIds.current[key] ?? { id: `${Date.now()}-${Math.random().toString(36).slice(2)}`, price: pack.price_toman };
    requestIds.current[key] = purchase;
    setPaying(pack.id); setError(""); setPaymentLink("");
    try {
      const result = await searchWalletApi.topup({ package_id: pack.id, request_id: purchase.id, gateway: selectedGateway,
        client: Platform.OS === "android" ? "android" : "web", expected_price_toman: purchase.price });
      if (!mounted.current || account.current !== expectedOwner) { popup?.close(); return; }
      if (result.status !== "pending") {
        popup?.close(); delete requestIds.current[key]; refresh();
        setError(result.status === "paid" ? isFa ? "این خرید قبلاً ثبت شده است؛ موجودی به‌روزرسانی شد." : "This purchase was already credited. Your balance has been refreshed."
          : isFa ? "پرداخت قبلی تکمیل نشد؛ برای شروع پرداخت تازه دوباره خرید بسته را انتخاب کنید." : "The previous payment did not complete. Select the package again for a new payment.");
        return;
      }
      if (Platform.OS === "web") {
        if (popup && !popup.closed) popup.location.href = result.payment_url;
        else setPaymentLink(result.payment_url);
      } else await Linking.openURL(result.payment_url);
    } catch (failure) {
      popup?.close();
      if (failure instanceof ApiError && failure.code === "AI_CREDIT_PRICE_CHANGED") {
        delete requestIds.current[key]; void wallet.refetch();
      }
      if (mounted.current && account.current === expectedOwner)
        setError(failure instanceof ApiError ? failure.message : isFa ? "آماده‌سازی پرداخت انجام نشد؛ دوباره تلاش کنید." : "Could not prepare payment. Please retry.");
    } finally { if (mounted.current && account.current === expectedOwner) setPaying(null); }
  };
  const card = { backgroundColor: colors.cardBg, borderWidth: 1, borderColor: colors.border, borderRadius: radius.card, padding: spacing.lg, gap: spacing.sm } as const;
  const paymentAvailable = !!data?.topups_enabled;
  return <>
    <Card testID="smart-search-wallet" style={{ marginBottom: spacing.md, gap: spacing.md, ...(compact ? {padding:10} : {}) }}>
      <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <View style={{ flex: 1, gap: 3 }}>
          {!compact ? <AppText size={12} muted>{isFa ? "اعتبار سرچ هوشمند" : "Smart search credits"}</AppText> : null}
          <AppText testID="search-credit-balance" size={compact ? 14 : 26} weight="900" color={exhausted || low ? colors.denyLabel : colors.accent}>
            {compact ? <AppText size={11} muted>{isFa ? "موجودی " : "Balance "}</AppText> : null}
            {amount(data?.available, isFa)} <AppText size={12}>{isFa ? "اعتبار" : "credits"}</AppText>
          </AppText>
        </View>
        <Pressable accessibilityRole="button" testID="search-credit-manage" onPress={() => setOpen(true)}
          style={({ pressed }) => ({ minHeight: 44, paddingHorizontal: spacing.lg, justifyContent: "center", borderRadius: radius.btn,
            backgroundColor: colors.accent, opacity: pressed ? 0.85 : 1 })}>
          <AppText size={12} weight="800" color={colors.onAccent}>{isFa ? "مدیریت و شارژ" : "Manage & top up"}</AppText>
        </Pressable>
      </View>
      {data ? <>
        {!compact ? <AppText size={12} muted>{isFa ? "مصرف ۳۰ روز گذشته: " : "Used in the last 30 days: "}{amount(data.usage_30_days.credits, isFa)} {isFa ? "اعتبار" : "credits"}</AppText> : null}
        {low || exhausted ? <View testID="search-credit-warning" style={{padding:10,borderRadius:10,backgroundColor:colors.denyLabel+"12",borderWidth:1,borderColor:colors.denyLabel+"40"}}><AppText size={12} weight="700" color={colors.denyLabel}>{exhausted ? isFa ? "⚑ اعتبار تمام شده؛ برای ادامه، بستهٔ اعتبار بخرید." : "⚑ Credits exhausted. Top up to continue." : isFa ? "⚑ اعتبار شما رو به پایان است." : "⚑ Your credits are running low."}</AppText></View> : null}
        {!data.billing_enabled ? <AppText size={11} muted>{isFa ? "در حال حاضر از اعتبار شما کم نمی‌شود." : "Credits are not being deducted yet."}</AppText> : !data.can_search ? <AppText size={12} color={colors.denyLabel}>{!data.pricing_ready ? isFa ? "تعرفهٔ سرویس موقتاً در دسترس نیست." : "Pricing is temporarily unavailable."
          : isFa ? "اعتبار قابل استفادهٔ شما تمام شده است؛ برای ادامه بستهٔ شارژ بخرید." : "You have no available credits left. Buy a package to continue."}</AppText> : null}
      </> : <Pressable accessibilityRole="button" onPress={() => void wallet.refetch()}><AppText size={11} muted>{wallet.isError ? isFa ? "دریافت اعتبار انجام نشد؛ تلاش دوباره" : "Could not load credits. Retry" : isFa ? "دریافت موجودی…" : "Loading credits…"}</AppText></Pressable>}
    </Card>
    <Modal visible={open} transparent animationType="fade" onRequestClose={() => { if (paying === null) setOpen(false); }}>
      <View style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "center", padding: 16 }}>
        <View style={[card, { maxHeight: "90%", width: "100%", maxWidth: 560, alignSelf: "center", gap: 14 }]}>
          <View style={{ flexDirection: row, alignItems: "center", gap: 12 }}>
            <AppText size={19} weight="900" style={{ flex: 1 }}>{isFa ? "اعتبار سرچ هوشمند" : "Smart search credits"}</AppText>
            <Pressable accessibilityRole="button" accessibilityLabel={isFa ? "بستن مدیریت اعتبار" : "Close credit management"} disabled={paying !== null}
              onPress={() => setOpen(false)} style={{ minWidth: 44, minHeight: 44, alignItems: "center", justifyContent: "center" }}><AppText size={22}>×</AppText></Pressable>
          </View>
          <ScrollView contentContainerStyle={{ gap: spacing.lg }}>
            <View style={{ gap: 6, backgroundColor: colors.softBg, padding: 14, borderRadius: 12 }}>
              <AppText size={12} weight="700" muted>{isFa ? "اعتبار قابل استفاده" : "Available credits"}</AppText>
              <AppText size={32} weight="900" color={colors.accent}>{amount(data?.available, isFa)} <AppText size={14}>{isFa ? "اعتبار" : "credits"}</AppText></AppText>
              <AppText size={12} muted>{isFa ? "اعتبار پس از پایان هر جست‌وجو کسر می‌شود." : "Credits are deducted after each search finishes."}</AppText>
              {compact && data ? <AppText size={12} muted>{isFa ? "مصرف ۳۰ روز گذشته: " : "Used in the last 30 days: "}{amount(data.usage_30_days.credits,isFa)} {isFa ? "اعتبار" : "credits"}</AppText> : null}
              {!data?.billing_enabled ? <AppText size={12} muted>{isFa ? "در حال حاضر از اعتبار شما کم نمی‌شود." : "Credits are not being deducted yet."}</AppText> : null}
            </View>
            <AppText size={14} weight="800">{isFa ? "شارژ اعتبار" : "Top up credits"}</AppText>
            <AppText size={12} muted>{isFa ? "بستهٔ موردنظر را انتخاب کنید؛ اعتبار پس از پرداخت به حساب شما اضافه می‌شود." : "Choose a package. Credits are added after payment is confirmed."}</AppText>
            <View testID="search-credit-packages" style={{ flexDirection: row, flexWrap: "wrap", gap: spacing.sm }}>
              {(data?.packages ?? []).map(pack => {
                const selected = packageToBuy?.id === pack.id;
                return <Pressable key={pack.id} testID={`search-credit-package-${pack.id}`} accessibilityRole="radio"
                  accessibilityState={{ checked: selected }} disabled={paying !== null} onPress={() => setSelectedPackage(pack.id)}
                  style={{ flexGrow: 1, flexBasis: 90, minHeight: 96, padding: spacing.md, gap: spacing.sm,
                    borderRadius: radius.input, borderWidth: 2, borderColor: selected ? colors.accent : colors.border,
                    backgroundColor: selected ? `${colors.accent}12` : colors.softBg, alignItems: "center", justifyContent: "center" }}>
                  <AppText size={20} weight="900" color={selected ? colors.accent : colors.ink}>{amount(pack.credits, isFa)}</AppText>
                  <AppText size={12} muted>{isFa ? "اعتبار" : "credits"}</AppText>
                  <AppText size={11} weight="700">{pack.price_toman > 0 ? `${amount(pack.price_toman, isFa)} ${isFa ? "تومان" : "toman"}` : isFa ? "به‌زودی" : "Coming soon"}</AppText>
                </Pressable>;
              })}
            </View>
            {!paymentAvailable ? <AppText size={13} muted>{isFa ? "خرید بسته در حال حاضر فعال نیست." : "Credit purchases are not available yet."}</AppText> : <>
              {data.gateways.length > 1 ? <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8 }}>{data.gateways.map(g => <Pressable key={g.kind} accessibilityRole="button"
                onPress={() => setGateway(g.kind)} style={{ padding: 10, borderRadius: 10, backgroundColor: selectedGateway === g.kind ? colors.accent : colors.softBg }}>
                <AppText size={12} color={selectedGateway === g.kind ? colors.onAccent : colors.ink}>{g.name}</AppText></Pressable>)}</View> : null}
              {packageToBuy ? <Pressable testID="search-credit-buy" accessibilityRole="button" disabled={paying !== null} onPress={() => void pay(packageToBuy)}
                style={({ pressed }) => ({ minHeight: 52, alignItems: "center", justifyContent: "center", backgroundColor: colors.accent,
                  borderRadius: radius.btn, opacity: paying !== null ? 0.6 : pressed ? 0.85 : 1 })}>
                <AppText size={14} weight="800" color={colors.onAccent}>{paying !== null ? isFa ? "آماده‌سازی پرداخت…" : "Preparing payment…"
                  : isFa ? `خرید ${amount(packageToBuy.credits, true)} اعتبار` : `Buy ${amount(packageToBuy.credits, false)} credits`}</AppText>
              </Pressable> : null}
              {!data.packages.length ? <AppText size={13} muted>{isFa ? "بستهٔ شارژی برای خرید موجود نیست." : "No credit packages are available."}</AppText> : null}
            </>}
            {error ? <AppText size={12} color={colors.denyLabel}>{error}</AppText> : null}
            {paymentLink ? <Pressable accessibilityRole="button" onPress={() => void Linking.openURL(paymentLink)}><AppText size={13} color={colors.accent}>{isFa ? "ادامهٔ پرداخت در درگاه" : "Continue to payment"}</AppText></Pressable> : null}
            <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}><AppText size={14} weight="800">{isFa ? "گردش اعتبار" : "Credit history"}</AppText>
              <Pressable accessibilityRole="button" onPress={refresh} style={{ minHeight: 44, justifyContent: "center" }}><AppText size={12} color={colors.accent}>{isFa ? "به‌روزرسانی" : "Refresh"}</AppText></Pressable></View>
            {history.data?.pending.map(item => <View key={item.id} style={{ padding: 12, backgroundColor: colors.softBg, borderRadius: 12, gap: 5 }}>
              <AppText size={12}>{item.status === "pending" ? isFa ? "مصرف در انتظار بررسی" : "Usage awaiting review" : isFa ? "جست‌وجو در حال اجرا" : "Search in progress"}</AppText>
              <AppText size={12} muted>{isFa ? "موجودی شما برای این بررسی قفل نمی‌شود." : "This review does not lock your balance."}</AppText>
            </View>)}
            {history.data?.transactions.map(entry => <View key={entry.id} style={{ paddingVertical: 10, borderBottomWidth: 1, borderColor: colors.border, gap: 5 }}>
              <View style={{ flexDirection: row, justifyContent: "space-between", gap: 10 }}><AppText size={13} weight="700">{isFa ? entry.label : entry.kind === "topup" ? "Credit purchase" : entry.kind === "search" ? "Smart search" : entry.kind === "initial" ? "Welcome credits" : "Credit adjustment"}</AppText>
                <AppText size={13} color={Number(entry.amount) < 0 ? colors.ink : colors.accent}>{amount(entry.amount, isFa)}</AppText></View>
              <AppText size={11} muted>{new Date(entry.created_at).toLocaleString(isFa ? "fa-IR" : "en-US")}</AppText>
              {entry.note ? <AppText size={11} muted>{entry.note}</AppText> : null}
            </View>)}
            {history.isLoading ? <AppText size={12} muted>{isFa ? "دریافت گردش اعتبار…" : "Loading history…"}</AppText> : history.isError ? <AppText size={12} muted>{isFa ? "دریافت گردش اعتبار انجام نشد." : "Could not load credit history."}</AppText>
              : !history.data?.transactions.length && !history.data?.pending.length ? <AppText size={12} muted>{isFa ? "هنوز تراکنشی ثبت نشده است." : "No transactions yet."}</AppText> : null}
            <View style={{ flexDirection: row, justifyContent: "space-between" }}>{offset > 0 ? <Pressable onPress={() => setOffset(Math.max(0, offset - 20))} accessibilityRole="button" style={{ minHeight: 44, justifyContent: "center" }}><AppText color={colors.accent}>{isFa ? "قبلی" : "Previous"}</AppText></Pressable> : null}
              {history.data?.next_offset !== null && history.data?.next_offset !== undefined ? <Pressable onPress={() => setOffset(history.data!.next_offset!)} accessibilityRole="button" style={{ minHeight: 44, justifyContent: "center" }}><AppText color={colors.accent}>{isFa ? "بعدی" : "Next"}</AppText></Pressable> : null}</View>
          </ScrollView>
        </View>
      </View>
    </Modal>
  </>;
}
