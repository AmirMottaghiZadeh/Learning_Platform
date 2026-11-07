import { useMutation, useQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { Pressable, TextInput, View } from "react-native";

import { ApiError } from "@/api/client";
import { LexicompDrug, LexicompInteraction } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { OfflineDownloadButton } from "@/components/offline/OfflineDownloadButton";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { Screen } from "@/components/primitives/Screen";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { lexicompSource } from "@/offline/sources";
import { StringKey } from "@/i18n/strings";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { TourTarget, useTour } from "@/tour/TourContext";
import { fontFamily } from "@/theme/fonts";
import { spacing } from "@/theme/tokens";
import { toneColors } from "@/theme/tone";
import { htmlToParagraphs } from "@/utils/html";
import { groupInteractions, InteractionGroup } from "@/utils/lexicompGroups";

const SEVERITY_LABEL: Record<string, StringKey> = {
  major: "lexicompSeverityMajor",
  moderate: "lexicompSeverityModerate",
  minor: "lexicompSeverityMinor",
};

const SEVERITY_TONE: Record<string, "deny" | "caution" | "special"> = {
  major: "deny",
  moderate: "caution",
  minor: "special",
};

/** Search-and-select two or more drugs, then check every interaction the
 * Lexicomp snapshot records between them -- same search UX as the UpToDate
 * screen, but selecting a result adds it to a running list instead of
 * navigating away. */
export function LexicompScreen() {
  const { t, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);

  const [q, setQ] = useState("");
  const query = useDebounced(q.trim());
  const [selected, setSelected] = useState<LexicompDrug[]>([]);

  const { data, isFetching, error } = useQuery({
    queryKey: ["lexicomp-search", query],
    queryFn: () => lexicompSource.search(query),
    enabled: query.length >= 2,
    retry: false,
  });

  const locked = error instanceof ApiError && error.status === 503;
  const rows = useMemo(() => data ?? [], [data]);
  useTour("lexicomp", true);
  const selectedGenericIds = useMemo(
    () => Array.from(new Set(selected.map((d) => d.generic_id))),
    [selected],
  );

  const check = useMutation({
    mutationFn: () => lexicompSource.checkInteractions(selectedGenericIds),
    // answered from the device when Lexicomp is downloaded, so no network needed
    networkMode: "always",
  });

  const addDrug = (drug: LexicompDrug) => {
    setSelected((cur) => (cur.some((d) => d.generic_id === drug.generic_id) ? cur : [...cur, drug]));
    setQ("");
    check.reset();
  };

  const removeDrug = (genericId: number) => {
    setSelected((cur) => cur.filter((d) => d.generic_id !== genericId));
    check.reset();
  };

  return (
    <Screen>
      <ScreenChrome
        title={t("lexicompScreenTitle")}
        onBack={goBack}
        tour="lexicomp"
        actions={<OfflineDownloadButton dataset="lexicomp" size={30} tourId="lexi.offline" />}
      />
      <AppText muted weight="600" size={12} style={{ marginBottom: 14 }}>
        {t("lexicompSourceNote")}
      </AppText>

      <TourTarget id="lexi.search" style={{ marginBottom: spacing.md }}>
      <View
        style={{
          flexDirection: row,
          alignItems: "center",
          gap: 8,
          backgroundColor: colors.inputBg,
          borderWidth: 1,
          borderColor: colors.trackBg,
          borderRadius: 14,
          paddingHorizontal: 14,
          paddingVertical: 12,
        }}
      >
        <AppText muted>⌕</AppText>
        <TextInput
          value={q}
          onChangeText={setQ}
          placeholder={t("lexicompSearchPlaceholder")}
          placeholderTextColor={colors.muted}
          style={{
            flex: 1,
            fontFamily: fontFamily("600"),
            fontSize: 13,
            color: colors.ink,
            textAlign: "left",
            writingDirection: "ltr",
            padding: 0,
          }}
        />
        {isFetching ? <AppText muted size={12}>…</AppText> : null}
      </View>
      </TourTarget>

      {query.length >= 2 && !locked ? (
        <View style={{ gap: 8, marginBottom: spacing.lg }}>
          {rows.length === 0 && !isFetching ? (
            <AppText muted weight="600" size={12} style={{ paddingVertical: 8 }}>
              {t("lexicompEmptyTitle")} — {t("lexicompEmptySub")}
            </AppText>
          ) : (
            rows.map((drug) => (
              <Pressable key={`${drug.kind}-${drug.id}`} onPress={() => addDrug(drug)}>
                <Card
                  soft
                  style={{ flexDirection: row, alignItems: "center", gap: 10, paddingVertical: 11 }}
                >
                  <AppText
                    weight="700"
                    size={13}
                    style={{ flex: 1, textAlign: "left", writingDirection: "ltr" }}
                  >
                    {drug.name}
                  </AppText>
                  <AppText weight="900" size={16} color={colors.accent}>
                    +
                  </AppText>
                </Card>
              </Pressable>
            ))
          )}
        </View>
      ) : null}

      {locked ? (
        <Card style={{ marginBottom: spacing.lg }}>
          <AppText weight="800" size={15} color={colors.accent}>
            {t("comingSoon")}
          </AppText>
          <AppText muted weight="600" size={13} style={{ marginTop: 6 }}>
            {t("lockedFeature")}
          </AppText>
        </Card>
      ) : null}

      {selected.length > 0 ? (
        <View style={{ marginBottom: spacing.lg }}>
          <AppText weight="800" size={13} muted style={{ marginBottom: 8 }}>
            {t("lexicompSelectedLabel")}
          </AppText>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
            {selected.map((drug) => (
              <Pressable
                key={drug.generic_id}
                onPress={() => removeDrug(drug.generic_id)}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  gap: 6,
                  backgroundColor: `${colors.accent}14`,
                  borderWidth: 1,
                  borderColor: colors.accent,
                  borderRadius: 999,
                  paddingVertical: 7,
                  paddingHorizontal: 12,
                }}
              >
                <AppText
                  weight="700"
                  size={12}
                  color={colors.accent}
                  style={{ textAlign: "left", writingDirection: "ltr" }}
                >
                  {drug.name}
                </AppText>
                <AppText weight="900" size={13} color={colors.accent}>
                  ×
                </AppText>
              </Pressable>
            ))}
          </View>

          {selected.length < 2 ? (
            <AppText muted weight="600" size={12} style={{ marginTop: 10 }}>
              {t("lexicompMinDrugsHint")}
            </AppText>
          ) : (
            <Pressable
              onPress={() => check.mutate()}
              style={{
                backgroundColor: colors.accent,
                borderRadius: 14,
                paddingVertical: 14,
                alignItems: "center",
                marginTop: 12,
              }}
            >
              <AppText weight="800" size={14} color={colors.onAccent}>
                {check.isPending ? "…" : t("lexicompCheckBtn")}
              </AppText>
            </Pressable>
          )}
        </View>
      ) : null}

      {check.isError ? (
        <AppText size={12} weight="700" color={colors.denyLabel} style={{ marginBottom: 12 }}>
          {t("lexicompCheckError")}
        </AppText>
      ) : null}

      {check.isSuccess ? (
        check.data.length === 0 ? (
          <Card style={{ alignItems: "center", paddingVertical: 26 }}>
            <AppText weight="800" size={14} center style={{ marginBottom: 6 }}>
              {t("lexicompNoInteractionsTitle")}
            </AppText>
            <AppText muted weight="600" size={12} center>
              {t("lexicompNoInteractionsSub")}
            </AppText>
          </Card>
        ) : (
          <View style={{ gap: 10 }}>
            {groupInteractions(check.data).map((group) => (
              <InteractionCard
                key={group.key}
                group={group}
              />
            ))}
          </View>
        )
      ) : null}
    </Screen>
  );
}

function InteractionCard({ group }: { group: InteractionGroup }) {
  const { t, isFa, n, row } = useLang();
  const { colors } = useTheme();
  const key = group.severity.toLowerCase();
  const tone = toneColors(SEVERITY_TONE[key] ?? "info", colors);
  const severityLabel = SEVERITY_LABEL[key] ? t(SEVERITY_LABEL[key]) : group.severity;

  return (
    <Card style={{ gap: 10 }}>
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
        <AppText
          weight="800"
          size={14}
          style={{ flex: 1, textAlign: "left", writingDirection: "ltr" }}
        >
          {group.names.join(" × ")}
        </AppText>
        <View
          style={{
            backgroundColor: tone.bg,
            borderWidth: 1,
            borderColor: tone.border,
            borderRadius: 999,
            paddingVertical: 4,
            paddingHorizontal: 10,
          }}
        >
          <AppText weight="800" size={11} color={tone.label}>
            {severityLabel}
          </AppText>
        </View>
      </View>

      <AppText muted size={12}>{isFa ? `${n(group.interactions.length)} نوع تداخل` : `${group.interactions.length} interaction rule(s)`}</AppText>
      {group.interactions.map((interaction, index) => (
        <View key={interaction.monograph_id} style={{ gap: 8, borderTopWidth: 1, borderTopColor: colors.sheetLine, paddingTop: 10 }}>
          <View style={{ flexDirection: row, justifyContent: "space-between", gap: 8 }}>
            <AppText weight="800" size={13}>{isFa ? `تداخل ${n(index + 1)}` : `Interaction ${index + 1}`}</AppText>
            <AppText muted size={12}>{SEVERITY_LABEL[interaction.severity.toLowerCase()] ? t(SEVERITY_LABEL[interaction.severity.toLowerCase()]) : interaction.severity}</AppText>
          </View>
          <InteractionDisclosure label={isFa ? "خلاصهٔ تداخل" : "Interaction summary"} text={interaction.summary} />
          <InteractionDisclosure label={t("lexicompManagementLabel")} text={interaction.management} />
          {interaction.discussion ? <InteractionDisclosure label={t("lexicompDiscussionLabel")} text={interaction.discussion} /> : null}
          {interaction.footnotes ? <InteractionDisclosure label={isFa ? "منابع و توضیحات" : "References and notes"} text={interaction.footnotes} /> : null}
        </View>
      ))}
    </Card>
  );
}

function InteractionDisclosure({ label, text }: { label: string; text: string }) {
  const [open, setOpen] = useState(false);
  const { colors } = useTheme();
  const { row, isFa } = useLang();
  return (
    <View style={{ borderWidth: 1, borderColor: colors.trackBg, borderRadius: 12, overflow: "hidden" }}>
      <Pressable onPress={() => setOpen((value) => !value)} accessibilityRole="button" accessibilityState={{ expanded: open }} accessibilityLabel={label} style={{ minHeight: 46, paddingHorizontal: 12, flexDirection: row, alignItems: "center", justifyContent: "space-between", backgroundColor: colors.softBg }}>
        <AppText weight="700" size={12}>{label}</AppText>
        <AppText muted>{open ? "−" : "+"}</AppText>
      </Pressable>
      {open ? <AppText size={13} style={{ padding: 12, lineHeight: 22, textAlign: "left", writingDirection: "ltr" }}>{htmlToParagraphs(text) || (isFa ? "در منبع توضیحی ثبت نشده است." : "No explanation in the source.")}</AppText> : null}
    </View>
  );
}
