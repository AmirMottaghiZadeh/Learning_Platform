import { useQuery } from "@tanstack/react-query";
import React from "react";
import { View } from "react-native";

import { billingApi } from "@/api/endpoints";
import { MyEntitlement } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { IconImage } from "@/components/primitives/IconImage";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { JALALI_MONTHS_FA, GREGORIAN_MONTHS_EN, msToGregorian, toJalali } from "@/utils/jalali";

const ENDING_SOON_DAYS = 5;

/** The plan that lasts longest: a permanent one first, then by end date. */
function mainPlan(entitlements: MyEntitlement[]): MyEntitlement | null {
  const plans = entitlements.filter((e) => e.plan_kind === "plan");
  if (!plans.length) return null;
  return [...plans].sort((a, b) => {
    if (a.ends_at === null) return -1;
    if (b.ends_at === null) return 1;
    return Date.parse(b.ends_at) - Date.parse(a.ends_at);
  })[0];
}

/** The learner's subscription: the plan, how many days are left (with a bar
 * over the whole term) and the end date; or "free" when there is none. */
export function SubscriptionCard() {
  const { colors } = useTheme();
  const { t, n, isFa, row } = useLang();
  const { data } = useQuery({ queryKey: ["billing-me"], queryFn: billingApi.me });
  const plan = data ? mainPlan(data.entitlements) : null;

  const endDate = (() => {
    if (!plan?.ends_at) return null;
    const g = msToGregorian(Date.parse(plan.ends_at));
    if (!isFa) return `${GREGORIAN_MONTHS_EN[g.gm - 1]} ${g.gd}, ${g.gy}`;
    const j = toJalali(g.gy, g.gm, g.gd);
    return `${n(j.jd)} ${JALALI_MONTHS_FA[j.jm - 1]} ${n(j.jy)}`;
  })();
  const totalDays = plan?.ends_at
    ? Math.max(1, Math.round((Date.parse(plan.ends_at) - Date.parse(plan.starts_at)) / 86_400_000))
    : 1;
  const left = plan?.days_left ?? null;
  const share = left === null ? 1 : Math.min(1, Math.max(0, left / totalDays));
  const endingSoon = left !== null && left <= ENDING_SOON_DAYS;

  return (
    <Card raised style={{ gap: 12 }}>
      <View style={{ flexDirection: row, alignItems: "center", gap: 12 }}>
        <IconImage name="profile-subscription" size={40} />
        <View style={{ flex: 1, gap: 2 }}>
          <AppText weight="700" size={12} muted>
            {t("subscriptionTitle")}
          </AppText>
          <AppText weight="900" size={17}>
            {plan ? plan.plan_name_fa : t("subscriptionFree")}
          </AppText>
        </View>
        {plan ? (
          <View style={{ backgroundColor: `${colors.accent}1f`, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 }}>
            <AppText weight="800" size={11.5} color={colors.accent}>
              {t("subscriptionActive")}
            </AppText>
          </View>
        ) : null}
      </View>

      {plan ? (
        <View style={{ gap: 8 }}>
          {left !== null ? (
            <View style={{ flexDirection: row, alignItems: "baseline", gap: 6 }}>
              <AppText weight="900" size={30} color={endingSoon ? "#D65858" : colors.ink}>
                {n(left)}
              </AppText>
              <AppText weight="700" size={13} muted>
                {t("subscriptionDaysLeft")}
              </AppText>
            </View>
          ) : (
            <AppText weight="800" size={14}>
              {t("subscriptionPermanent")}
            </AppText>
          )}
          <View style={{ height: 8, borderRadius: 4, backgroundColor: colors.trackBg, overflow: "hidden", flexDirection: row }}>
            <View style={{ width: `${share * 100}%`, backgroundColor: endingSoon ? "#D65858" : colors.accent, borderRadius: 4 }} />
          </View>
          <View style={{ flexDirection: row, justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
            <AppText weight="600" size={12} muted>
              {endDate ? t("subscriptionUntil").replace("{date}", endDate) : ""}
            </AppText>
            {plan.source === "trial" ? (
              <AppText weight="700" size={12} color={colors.accent}>
                {t("subscriptionTrial")}
              </AppText>
            ) : null}
          </View>
          {endingSoon ? (
            <AppText weight="700" size={12} color="#D65858">
              {t("subscriptionEndingSoon")}
            </AppText>
          ) : null}
        </View>
      ) : (
        <AppText weight="600" size={12.5} muted style={{ lineHeight: 20 }}>
          {t("subscriptionFreeHint")}
        </AppText>
      )}
    </Card>
  );
}
