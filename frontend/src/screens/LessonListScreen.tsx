import { useQuery } from "@tanstack/react-query";
import React from "react";
import { Pressable, ScrollView, View } from "react-native";

import { lessonsApi } from "@/api/endpoints";
import type { AtcGroup, ChapterDrug } from "@/api/types";
import { ChromeButton, LangToggleButton } from "@/components/ScreenChrome";
import { useBleedTop } from "@/components/AppShell";
import { useNavClearance } from "@/components/BottomNav";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";

type ListItem =
  | { kind: "group"; group: AtcGroup; count: number; first: boolean }
  | { kind: "drug"; drug: ChapterDrug; index: number; grouped: boolean; firstInGroup: boolean; lastInGroup: boolean };

/** The chapter's drugs (already ordered by ATC level-4 class) with a header
 *  item in front of each class, so the list reads as sections: each class
 *  a solid band over one card holding its drugs. The band and the rows stay
 *  separate items so the band can stick to the top while its drugs scroll. */
function withGroupHeaders(drugs: ChapterDrug[]): ListItem[] {
  const items: ListItem[] = [];
  let current = "";
  let header: Extract<ListItem, { kind: "group" }> | null = null;
  drugs.forEach((drug, index) => {
    const code = drug.atc_group?.code ?? "";
    if (drug.atc_group && code !== current) {
      header = { kind: "group", group: drug.atc_group, count: 0, first: items.length === 0 };
      items.push(header);
    }
    current = code;
    const grouped = !!drug.atc_group;
    if (grouped && header) header.count += 1;
    const next = drugs[index + 1];
    items.push({
      kind: "drug",
      drug,
      index,
      grouped,
      firstInGroup: grouped && items[items.length - 1]?.kind === "group",
      lastInGroup: grouped && (next?.atc_group?.code ?? "") !== code,
    });
  });
  return items;
}

export function LessonListScreen() {
  const { t, isFa, n, row } = useLang();
  const { colors } = useTheme();
  const bleedTop = useBleedTop(true);
  const navClearance = useNavClearance(24);
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const code = String(useNav((s) => s.params.code ?? ""));

  const { data, isLoading, isError } = useQuery({
    queryKey: ["chapter", code],
    queryFn: () => lessonsApi.chapter(code),
    enabled: !!code,
  });

  const items = withGroupHeaders(data?.drugs ?? []);
  const headerIndices = items.flatMap((item, i) => (item.kind === "group" ? [i] : []));

  return (
    <View style={{ flex: 1, backgroundColor: colors.cardBg }}>
      <View style={{ paddingHorizontal: 22, paddingTop: 18 + bleedTop }}>
        <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
          <ChromeButton onPress={goBack} size={30}>
            <AppText weight="800" size={15} color={colors.ink}>
              {isFa ? "›" : "‹"}
            </AppText>
          </ChromeButton>
          <LangToggleButton />
        </View>

        {isLoading ? null : isError || !data ? (
          <>
            <AppText weight="900" size={22} style={{ marginTop: 16 }}>
              {t("emptyDrugsTitle")}
            </AppText>
            <AppText muted weight="600" size={13} style={{ marginTop: 6 }}>
              {t("emptyDrugsSub")}
            </AppText>
          </>
        ) : (
          <>
            <AppText
              weight="900"
              size={10}
              color={colors.accent}
              style={{ marginTop: 16, letterSpacing: 1.4 }}
            >
              {(isFa ? data.group_name_fa : data.group_name_en).toUpperCase()}
            </AppText>
            <AppText weight="900" size={24} style={{ marginTop: 6, lineHeight: 34 }}>
              {isFa ? data.name_fa : data.name_en}
            </AppText>
            <AppText weight="700" size={12.5} muted style={{ marginTop: 5 }}>
              {data.code} · {isFa ? data.anatomical_name_fa : data.anatomical_name_en} ·{" "}
              {n(data.drugs.length)} {t("lessonsUnit")}
            </AppText>
            {data.topics.length > 1 ? (
              <AppText weight="600" size={11.5} color={colors.accent} style={{ marginTop: 6 }}>
                {t("alsoRelevantTo")}:{" "}
                {data.topics
                  .slice(1)
                  .map((topic) => (isFa ? topic.name_fa : topic.name_en))
                  .join(isFa ? "، " : ", ")}
              </AppText>
            ) : null}
          </>
        )}
        <View style={{ height: 1, backgroundColor: colors.sheetLine, marginTop: 16 }} />
      </View>

      {isLoading ? (
        <LoadingState />
      ) : (
        <ScrollView
          style={{ flex: 1 }}
          stickyHeaderIndices={headerIndices}
          contentContainerStyle={{ padding: 22, paddingTop: 14, paddingBottom: navClearance }}
          showsVerticalScrollIndicator={false}
        >
          {items.map((item) => {
            if (item.kind === "group") {
              const { group } = item;
              const name = isFa && group.name_fa ? group.name_fa : group.name_en;
              const sub = isFa && group.name_fa ? group.name_en : "";
              return (
                // The class's band: the app's accent, so a class name can
                // never be mistaken for one of its drugs.
                <View
                  key={`g-${group.code}`}
                  style={{
                    flexDirection: row,
                    alignItems: "center",
                    gap: 10,
                    marginTop: item.first ? 0 : 14,
                    backgroundColor: colors.accent,
                    borderTopLeftRadius: 16,
                    borderTopRightRadius: 16,
                    paddingVertical: 11,
                    paddingHorizontal: 14,
                  }}
                >
                  <View
                    style={{
                      backgroundColor: colors.onAccentChip,
                      borderWidth: 1,
                      borderColor: colors.onAccentChipBorder,
                      borderRadius: 8,
                      paddingHorizontal: 8,
                      paddingVertical: 2,
                    }}
                  >
                    <AppText
                      weight="800"
                      size={11.5}
                      color={colors.onAccent}
                      style={{ writingDirection: "ltr", letterSpacing: 0.3 }}
                    >
                      {group.code}
                    </AppText>
                  </View>
                  <View style={{ flex: 1 }}>
                    <AppText weight="800" size={14.5} color={colors.onAccent} style={{ lineHeight: 22 }}>
                      {name}
                    </AppText>
                    {sub ? (
                      <AppText weight="600" size={11} color={colors.onAccentSub} style={{ writingDirection: "ltr" }}>
                        {sub}
                      </AppText>
                    ) : null}
                  </View>
                  <AppText weight="700" size={11.5} color={colors.onAccentSub}>
                    {isFa ? `${n(item.count)} دارو` : `${item.count} ${item.count === 1 ? "drug" : "drugs"}`}
                  </AppText>
                </View>
              );
            }
            const { drug, index, grouped, firstInGroup, lastInGroup } = item;
            const done = data?.progress.read_drug_slugs.includes(drug.slug);
            return (
              <Pressable
                key={drug.slug}
                onPress={() => navigate("lessonDetail", { code, slug: drug.slug })}
                style={
                  grouped
                    ? {
                        // one card under the band: rows split by hairlines
                        flexDirection: row,
                        alignItems: "center",
                        gap: 12,
                        backgroundColor: colors.softBg,
                        paddingVertical: 13,
                        paddingHorizontal: 14,
                        borderTopWidth: firstInGroup ? 0 : 1,
                        borderTopColor: colors.sheetLine,
                        borderBottomLeftRadius: lastInGroup ? 16 : 0,
                        borderBottomRightRadius: lastInGroup ? 16 : 0,
                      }
                    : {
                        flexDirection: row,
                        alignItems: "center",
                        gap: 12,
                        backgroundColor: colors.softBg,
                        borderRadius: 14,
                        padding: 14,
                        marginTop: index === 0 ? 0 : 10,
                      }
                }
              >
                <View
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 9,
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: done ? colors.accent : colors.cardBg,
                    borderWidth: 1,
                    borderColor: colors.trackBg,
                  }}
                >
                  <AppText weight="800" size={12} color={done ? colors.onAccent : colors.muted}>
                    {done ? "✓" : n(index + 1)}
                  </AppText>
                </View>
                <View style={{ flex: 1 }}>
                  <AppText weight="800" size={14}>
                    {drug.name}
                  </AppText>
                  {drug.pharm_classes.length ? (
                    <AppText muted weight="600" size={12} numberOfLines={1} style={{ marginTop: 2 }}>
                      {drug.pharm_classes.join(" · ")}
                    </AppText>
                  ) : null}
                </View>
                <AppText muted size={13}>
                  {isFa ? "‹" : "›"}
                </AppText>
              </Pressable>
            );
          })}
        </ScrollView>
      )}
    </View>
  );
}
