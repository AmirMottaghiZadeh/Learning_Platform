import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { AppState, Linking, Platform, Pressable, TextInput, View } from "react-native";

import { ApiError } from "@/api/client";
import { billingApi } from "@/api/endpoints";
import { BillingOrder, CatalogPlan, PlanFeatureItem, PlanPrice, PriceQuote } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { SubscriptionCard } from "@/components/profile/SubscriptionCard";
import { useLang } from "@/i18n/LanguageProvider";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";

const isPersian = (text?: string) => !!text && /[؀-ۿ]/.test(text);

/** 300000 -> "۳۰۰٬۰۰۰" (fa) / "300,000" (en). */
function useMoney() {
  const { n, isFa } = useLang();
  return (value: number) => n(String(Math.round(value)).replace(/\B(?=(\d{3})+(?!\d))/g, isFa ? "٬" : ","));
}

// No "·" between words and numbers: next to a Persian digit it reads as a
// zero ("۳۰ · مقاله" looks like "۳۰۰").
function featureLine(f: PlanFeatureItem, n: (v: string | number) => string): string {
  if (f.label_fa) return f.label_fa;
  if (f.limit === null) return f.name_fa;
  return `${f.name_fa} (${[n(f.limit), f.unit_fa, f.period_fa].filter(Boolean).join(" ")})`;
}

type Choice = { plan: CatalogPlan; price: PlanPrice };

/** Buying in the app: every plan on sale with what it gives and its prices
 * per duration; then the chosen one with an optional discount code, the
 * gateway, and online payment. The payment page opens in the browser (the
 * site hands the buyer to the gateway); back in the app, the order's outcome
 * is read again until it is known. */
export function PlansScreen() {
  const { t, row, isFa } = useLang();
  const { colors } = useTheme();
  const money = useMoney();
  const goBack = useNav((s) => s.goBack);
  const isGuest = useAuth((s) => !!s.user?.is_guest);
  const queryClient = useQueryClient();

  const { data: catalog, isLoading, isError, refetch } = useQuery({ queryKey: ["billing-catalog"], queryFn: billingApi.catalog });
  const [pick, setPick] = useState<Choice | null>(null);
  const [code, setCode] = useState("");
  const [quote, setQuote] = useState<{ code: string; value: PriceQuote } | null>(null);
  const [codeError, setCodeError] = useState("");
  const [gateway, setGateway] = useState<string>("");
  const [payError, setPayError] = useState("");
  // the order sent to the gateway, until its outcome is known
  const [orderId, setOrderId] = useState<number | null>(null);

  const gateways = catalog?.gateways ?? [];
  const chosenGateway = gateways.some((g) => g.kind === gateway) ? gateway : gateways[0]?.kind ?? "";
  const salesOpen = catalog?.sales_enabled !== false;
  const sections = useMemo(
    () => [
      { title: t("plansTitlePlans"), items: (catalog?.plans ?? []).filter((p) => p.prices.length) },
      { title: t("plansTitleProducts"), items: (catalog?.products ?? []).filter((p) => p.prices.length) },
    ].filter((s) => s.items.length),
    [catalog, t],
  );

  // the first price of the first plan, until one is picked
  useEffect(() => {
    if (pick || !sections.length) return;
    const plan = sections[0].items[0];
    setPick({ plan, price: plan.prices[0] });
  }, [sections, pick]);

  const choose = (plan: CatalogPlan, price: PlanPrice) => {
    setPick({ plan, price });
    setQuote(null);
    setCodeError("");
    setPayError("");
  };

  const quoteMutation = useMutation({
    mutationFn: () => billingApi.quote(pick!.price.id, code.trim()),
    onSuccess: (value) => {
      setQuote({ code: code.trim(), value });
      setCodeError("");
    },
    onError: (error) => {
      setQuote(null);
      setCodeError(error instanceof ApiError && isPersian(error.message) ? error.message : t("plansCodeInvalid"));
    },
  });

  const checkoutMutation = useMutation({
    mutationFn: () =>
      billingApi.checkout({
        price_id: pick!.price.id,
        discount_code: quote?.code ?? "",
        gateway: chosenGateway,
        client: Platform.OS === "web" ? "web" : "android",
      }),
    onSuccess: async (result) => {
      setPayError("");
      if (result.status === "paid") {
        setOrderId(result.order_id);
        await queryClient.invalidateQueries({ queryKey: ["billing-orders"] });
        await queryClient.invalidateQueries({ queryKey: ["billing-me"] });
        return;
      }
      setOrderId(result.order_id);
      if (Platform.OS === "web") {
        window.location.assign(result.payment_url);
      } else {
        Linking.openURL(result.payment_url).catch(() => setPayError(t("plansOpenFailed")));
      }
    },
    onError: (error) => {
      setPayError(error instanceof ApiError && isPersian(error.message) ? error.message : t("plansPayFailed"));
    },
  });

  // the order's outcome: read when the app comes back from the browser, and
  // every few seconds while it is still pending
  const { data: orders, refetch: refetchOrders, isFetching: checking } = useQuery({
    queryKey: ["billing-orders"],
    queryFn: billingApi.orders,
    enabled: orderId !== null,
    refetchInterval: (query) => {
      const order = query.state.data?.find((o) => o.id === orderId);
      return order && order.status === "pending" ? 5000 : false;
    },
  });
  const order: BillingOrder | undefined = orders?.find((o) => o.id === orderId);
  const lastStatus = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (order?.status === "paid" && lastStatus.current !== "paid") {
      void queryClient.invalidateQueries({ queryKey: ["billing-me"] });
    }
    lastStatus.current = order?.status;
  }, [order?.status, queryClient]);
  useEffect(() => {
    if (orderId === null) return;
    const sub = AppState.addEventListener("change", (state) => {
      if (state === "active") void refetchOrders();
    });
    return () => sub.remove();
  }, [orderId, refetchOrders]);

  if (isLoading) return <LoadingState />;

  const payable = quote?.value.payable_toman ?? pick?.price.price_toman ?? 0;

  return (
    <Screen>
      <ScreenChrome title={t("plansScreenTitle")} onBack={goBack} />

      {isGuest ? (
        <Card raised>
          <AppText weight="700" size={14} style={{ lineHeight: 24 }}>
            {t("plansGuest")}
          </AppText>
        </Card>
      ) : (
        <View style={{ gap: 14 }}>
          <SubscriptionCard />

          {orderId !== null ? (
            <OrderStatusCard order={order} checking={checking} onCheck={() => void refetchOrders()} onDone={() => setOrderId(null)} />
          ) : null}

          {isError ? (
            <Card raised style={{ gap: 10, alignItems: "center" }}>
              <AppText weight="700" size={13} muted>
                {t("loadFailed")}
              </AppText>
              <Pressable onPress={() => void refetch()} style={{ paddingHorizontal: 16, paddingVertical: 8 }}>
                <AppText weight="800" size={13} color={colors.accent}>
                  {t("retry")}
                </AppText>
              </Pressable>
            </Card>
          ) : null}

          {!salesOpen ? (
            <View style={{ backgroundColor: colors.cautBg, borderColor: colors.cautBorder, borderWidth: 1, borderRadius: 14, padding: 14 }}>
              <AppText weight="700" size={13} color={colors.cautInk} style={{ lineHeight: 22 }}>
                {t("plansSalesPaused")}
              </AppText>
            </View>
          ) : null}

          {catalog && !sections.length ? (
            <Card raised>
              <AppText weight="700" size={13} muted style={{ lineHeight: 22 }}>
                {t("plansNone")}
              </AppText>
            </Card>
          ) : null}

          {sections.map((section) => (
            <View key={section.title} style={{ gap: 10 }}>
              <AppText weight="800" size={13} muted>
                {section.title}
              </AppText>
              {section.items.map((plan) => (
                <PlanCard
                  key={plan.id}
                  plan={plan}
                  picked={pick?.plan.id === plan.id ? pick.price.id : null}
                  onPick={(price) => choose(plan, price)}
                />
              ))}
            </View>
          ))}

          {pick && salesOpen ? (
            <Card raised style={{ gap: 14 }}>
              <View style={{ gap: 4 }}>
                <AppText weight="700" size={12} muted>
                  {t("plansYourChoice")}
                </AppText>
                <AppText weight="900" size={16}>
                  {pick.plan.name_fa}
                </AppText>
                <AppText weight="700" size={13} color={colors.accent}>
                  {pick.price.duration_label}
                </AppText>
              </View>

              <View style={{ gap: 6 }}>
                <AppText weight="700" size={12.5}>
                  {t("plansDiscountLabel")}
                </AppText>
                <View style={{ flexDirection: row, gap: 8 }}>
                  <TextInput
                    value={code}
                    onChangeText={(v) => {
                      setCode(v);
                      setCodeError("");
                      if (quote && v.trim() !== quote.code) setQuote(null);
                    }}
                    placeholder={t("plansDiscountPlaceholder")}
                    placeholderTextColor={colors.muted}
                    autoCapitalize="characters"
                    autoCorrect={false}
                    style={{
                      flex: 1,
                      minWidth: 0,
                      height: 46,
                      borderRadius: 12,
                      borderWidth: 1,
                      borderColor: codeError ? "#D65858" : colors.trackBg,
                      backgroundColor: colors.inputBg,
                      paddingHorizontal: 12,
                      fontFamily: fontFamily("700"),
                      fontSize: 14,
                      color: colors.ink,
                      textAlign: code ? "left" : isFa ? "right" : "left",
                      writingDirection: code ? "ltr" : undefined,
                      ...(Platform.OS === "web" ? ({ outlineStyle: "none" } as object) : null),
                    }}
                  />
                  <Pressable
                    onPress={() => quoteMutation.mutate()}
                    disabled={!code.trim() || quoteMutation.isPending}
                    style={{
                      height: 46,
                      paddingHorizontal: 16,
                      borderRadius: 12,
                      alignItems: "center",
                      justifyContent: "center",
                      backgroundColor: colors.softBg,
                      borderWidth: 1,
                      borderColor: colors.trackBg,
                      opacity: !code.trim() ? 0.5 : 1,
                    }}
                  >
                    <AppText weight="800" size={13} color={colors.accent}>
                      {quoteMutation.isPending ? "…" : t("plansDiscountApply")}
                    </AppText>
                  </Pressable>
                </View>
                {codeError ? (
                  <AppText weight="700" size={12} color="#D65858">
                    {codeError}
                  </AppText>
                ) : quote ? (
                  <AppText weight="700" size={12} color={colors.accent}>
                    {t("plansDiscountApplied")}
                  </AppText>
                ) : null}
              </View>

              <View style={{ gap: 8, backgroundColor: colors.softBg, borderRadius: 14, padding: 12 }}>
                <SumRow label={t("plansAmount")} value={`${money(quote?.value.amount_toman ?? pick.price.price_toman)} ${t("plansToman")}`} />
                {quote && quote.value.discount_toman > 0 ? (
                  <SumRow label={t("plansDiscount")} value={`− ${money(quote.value.discount_toman)} ${t("plansToman")}`} color={colors.accent} />
                ) : null}
                <View style={{ height: 1, backgroundColor: colors.trackBg }} />
                <SumRow label={t("plansPayable")} value={`${money(payable)} ${t("plansToman")}`} strong />
              </View>

              {payable > 0 && gateways.length > 1 ? (
                <View style={{ gap: 8 }}>
                  <AppText weight="700" size={12.5}>
                    {t("plansGateway")}
                  </AppText>
                  <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8 }}>
                    {gateways.map((g) => {
                      const on = g.kind === chosenGateway;
                      return (
                        <Pressable
                          key={g.kind}
                          onPress={() => setGateway(g.kind)}
                          accessibilityRole="radio"
                          accessibilityState={{ selected: on }}
                          style={{
                            paddingHorizontal: 14,
                            paddingVertical: 9,
                            borderRadius: 12,
                            borderWidth: on ? 2 : 1,
                            borderColor: on ? colors.accent : colors.trackBg,
                            backgroundColor: on ? `${colors.accent}14` : colors.cardBg,
                          }}
                        >
                          <AppText weight={on ? "800" : "700"} size={13} color={on ? colors.accent : colors.ink}>
                            {g.name}
                          </AppText>
                        </Pressable>
                      );
                    })}
                  </View>
                </View>
              ) : null}

              {payable > 0 && !gateways.length ? (
                <AppText weight="700" size={12.5} color="#D65858" style={{ lineHeight: 21 }}>
                  {t("plansNoGateway")}
                </AppText>
              ) : null}

              <Pressable
                onPress={() => checkoutMutation.mutate()}
                disabled={checkoutMutation.isPending || (payable > 0 && !gateways.length)}
                style={{
                  height: 52,
                  borderRadius: 16,
                  backgroundColor: colors.accent,
                  alignItems: "center",
                  justifyContent: "center",
                  opacity: checkoutMutation.isPending || (payable > 0 && !gateways.length) ? 0.6 : 1,
                }}
              >
                <AppText weight="900" size={15} color={colors.onAccent}>
                  {checkoutMutation.isPending ? "…" : payable > 0 ? t("plansPayOnline") : t("plansActivate")}
                </AppText>
              </Pressable>
              {payError ? (
                <AppText weight="700" size={12.5} color="#D65858" center style={{ lineHeight: 21 }}>
                  {payError}
                </AppText>
              ) : null}
              <AppText weight="600" size={11.5} muted center style={{ lineHeight: 19 }}>
                {t("plansPayNote")}
              </AppText>
            </Card>
          ) : null}
        </View>
      )}
    </Screen>
  );
}

function SumRow({ label, value, strong, color }: { label: string; value: string; strong?: boolean; color?: string }) {
  const { row } = useLang();
  const { colors } = useTheme();
  return (
    <View style={{ flexDirection: row, justifyContent: "space-between", alignItems: "center", gap: 8 }}>
      <AppText weight={strong ? "800" : "600"} size={strong ? 14 : 13} muted={!strong}>
        {label}
      </AppText>
      <AppText weight={strong ? "900" : "700"} size={strong ? 16 : 13} color={color ?? colors.ink}>
        {value}
      </AppText>
    </View>
  );
}

/** One plan: badge, name, tagline, what it gives, and a choice per duration. */
function PlanCard({ plan, picked, onPick }: { plan: CatalogPlan; picked: number | null; onPick: (price: PlanPrice) => void }) {
  const { t, n, row } = useLang();
  const { colors, shadows } = useTheme();
  const money = useMoney();
  const on = picked !== null;
  const price = plan.prices.find((p) => p.id === picked) ?? plan.prices[0];
  const lines = [...plan.features.filter((f) => f.is_listed).map((f) => featureLine(f, n)), ...plan.extra_lines];

  return (
    <Pressable
      onPress={() => onPick(price)}
      style={[
        {
          backgroundColor: colors.cardBg,
          borderRadius: 20,
          padding: 16,
          gap: 12,
          borderWidth: 2,
          borderColor: on ? colors.accent : "transparent",
        },
        shadows.raisedSm,
      ]}
    >
      <View style={{ flexDirection: row, alignItems: "flex-start", justifyContent: "space-between", gap: 10 }}>
        <View style={{ flex: 1, gap: 4 }}>
          <AppText weight="900" size={17}>
            {plan.name_fa}
          </AppText>
          {plan.tagline_fa ? (
            <AppText weight="600" size={12.5} muted style={{ lineHeight: 20 }}>
              {plan.tagline_fa}
            </AppText>
          ) : null}
        </View>
        {plan.badge_fa ? (
          <View style={{ backgroundColor: colors.accent, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 }}>
            <AppText weight="800" size={11} color={colors.onAccent}>
              {plan.badge_fa}
            </AppText>
          </View>
        ) : null}
      </View>

      <View style={{ flexDirection: row, alignItems: "baseline", gap: 6, flexWrap: "wrap" }}>
        <AppText weight="900" size={22} color={colors.accent}>
          {money(price.price_toman)}
        </AppText>
        <AppText weight="700" size={12} muted>
          {`${t("plansToman")} / ${price.duration_label}`}
        </AppText>
        {price.compare_at_toman && price.compare_at_toman > price.price_toman ? (
          <AppText weight="700" size={12} muted style={{ textDecorationLine: "line-through" }}>
            {money(price.compare_at_toman)}
          </AppText>
        ) : null}
        {price.label_fa ? (
          <View style={{ backgroundColor: `${colors.accent}1A`, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 2 }}>
            <AppText weight="800" size={11} color={colors.accent}>
              {price.label_fa}
            </AppText>
          </View>
        ) : null}
      </View>

      {plan.prices.length > 1 ? (
        <View style={{ flexDirection: row, flexWrap: "wrap", gap: 8 }}>
          {plan.prices.map((p) => {
            const chosen = on && p.id === price.id;
            return (
              <Pressable
                key={p.id}
                onPress={() => onPick(p)}
                accessibilityRole="radio"
                accessibilityState={{ selected: chosen }}
                style={{
                  paddingHorizontal: 12,
                  paddingVertical: 8,
                  borderRadius: 12,
                  borderWidth: chosen ? 2 : 1,
                  borderColor: chosen ? colors.accent : colors.trackBg,
                  backgroundColor: chosen ? `${colors.accent}14` : colors.softBg,
                  alignItems: "center",
                  gap: 2,
                }}
              >
                <AppText weight="800" size={12.5} color={chosen ? colors.accent : colors.ink}>
                  {p.duration_label}
                </AppText>
                <AppText weight="600" size={11} muted>
                  {money(p.price_toman)}
                </AppText>
              </Pressable>
            );
          })}
        </View>
      ) : null}

      {plan.description_fa ? (
        <AppText weight="500" size={12.5} color={colors.proseInk} style={{ lineHeight: 21 }}>
          {plan.description_fa}
        </AppText>
      ) : null}

      {lines.length ? (
        <View style={{ gap: 7 }}>
          {lines.map((line) => (
            <View key={line} style={{ flexDirection: row, alignItems: "flex-start", gap: 8 }}>
              <AppText weight="900" size={13} color={colors.accent} style={{ lineHeight: 21 }}>
                ✓
              </AppText>
              <AppText weight="600" size={13} style={{ flex: 1, lineHeight: 21 }}>
                {line}
              </AppText>
            </View>
          ))}
        </View>
      ) : null}
    </Pressable>
  );
}

/** Where the payment stands once the buyer has gone to the gateway. */
function OrderStatusCard({
  order,
  checking,
  onCheck,
  onDone,
}: {
  order: BillingOrder | undefined;
  checking: boolean;
  onCheck: () => void;
  onDone: () => void;
}) {
  const { t, n } = useLang();
  const { colors } = useTheme();
  const status = order?.status ?? "pending";
  const tone =
    status === "paid"
      ? { bg: `${colors.accent}14`, border: colors.accent, ink: colors.accent, title: t("plansPaidTitle") }
      : status === "pending"
        ? { bg: colors.cautBg, border: colors.cautBorder, ink: colors.cautInk, title: t("plansPendingTitle") }
        : { bg: colors.denyBg, border: colors.denyBorder, ink: colors.denyInk, title: t("plansFailedTitle") };
  return (
    <View style={{ backgroundColor: tone.bg, borderColor: tone.border, borderWidth: 1, borderRadius: 16, padding: 14, gap: 8 }}>
      <AppText weight="900" size={15} color={tone.ink}>
        {tone.title}
      </AppText>
      <AppText weight="600" size={12.5} color={tone.ink} style={{ lineHeight: 21 }}>
        {status === "paid"
          ? t("plansPaidSub").replace("{plan}", order?.plan_name_fa ?? "")
          : status === "pending"
            ? t("plansPendingSub")
            : isPersian(order?.error)
              ? order!.error!
              : t("plansFailedSub")}
      </AppText>
      {order?.ref_id ? (
        <AppText weight="700" size={12} color={tone.ink}>
          {`${t("plansRefId")}: ${order.ref_id}`}
        </AppText>
      ) : null}
      {order ? (
        <AppText weight="600" size={11.5} muted>
          {`${t("plansOrder")} ${n(order.id)}`}
        </AppText>
      ) : null}
      <Pressable onPress={status === "pending" ? onCheck : onDone} style={{ alignSelf: "flex-start", paddingVertical: 4 }}>
        <AppText weight="800" size={13} color={tone.ink}>
          {status === "pending" ? (checking ? "…" : t("plansCheckAgain")) : t("dismiss")}
        </AppText>
      </Pressable>
    </View>
  );
}
