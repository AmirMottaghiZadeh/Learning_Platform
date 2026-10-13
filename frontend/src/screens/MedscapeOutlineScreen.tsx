import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { Pressable, ScrollView, View } from "react-native";

import { medscapeApi } from "@/api/endpoints";
import { BackGlyph, BandButton, BandLangToggle, BandSpacer, useBandColors } from "@/components/article/Band";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useReader } from "@/store/reader";
import { useTheme } from "@/theme/ThemeProvider";
import { layout } from "@/theme/tokens";
import { buildMedscapeModel, summaryTop, tocLabel } from "@/utils/medscapeArticle";

const LTR = { textAlign: "left" as const, writingDirection: "ltr" as const };

/** A guideline/disease article's home page (design option 3): the teal band
 * with the title and the article's counts, a jump to its summary section
 * when it has one, and the numbered table of contents. Opening a section
 * goes to the reader at that section; the button below picks up where the
 * reader was last left. */
export function MedscapeOutlineScreen() {
  const { t, n, row } = useLang();
  const { colors } = useTheme();
  const band = useBandColors();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const slug = String(useNav((s) => s.params.slug ?? ""));
  const lastIndex = useReader((s) => s.lastSection[`medscape:${slug}`]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["medscape-article", slug],
    queryFn: () => medscapeApi.detail(slug),
    enabled: !!slug,
  });

  const model = useMemo(() => (data ? buildMedscapeModel(data.sections) : null), [data]);
  const lastTop = model?.tops.find((top) => top.index === lastIndex) ?? null;
  const [expanded, setExpanded] = useState<string | null>(null);
  const openPath = expanded ?? lastTop?.path ?? null;

  const read = (path?: string) => navigate("medscapeArticle", { slug, path });

  if (isLoading) return <LoadingState />;

  const summary = model ? summaryTop(model) : null;
  // English like the rest of the band's article text, so it never mixes
  // directions on one line.
  const eyebrow = data
    ? [data.kind === "guideline" ? "Guideline" : "Disease", ...Array.from(new Set(data.categories.map((c) => c.specialty)))]
        // guideline articles are filed under a "Guidelines" specialty, which
        // would only repeat the kind
        .filter((part, i) => !!part && (i === 0 || !/^guidelines?$/i.test(part.trim())))
        .join(" · ")
        .toUpperCase()
    : "";

  return (
    <View style={{ flex: 1, backgroundColor: colors.appBg }}>
      <View style={{ backgroundColor: band.bg, paddingHorizontal: 18, paddingTop: 16, paddingBottom: 18, gap: 12 }}>
        <View style={{ flexDirection: row, alignItems: "center" }}>
          <BandButton onPress={goBack} label="back">
            <BackGlyph color={band.ink} />
          </BandButton>
          <BandSpacer />
          <BandLangToggle />
        </View>

        {data ? (
          <>
            <View style={{ gap: 6 }}>
              {eyebrow ? (
                <AppText weight="800" size={10.5} color={band.eyebrow} style={[LTR, { letterSpacing: 1.2, lineHeight: 16 }]}>
                  {eyebrow}
                </AppText>
              ) : null}
              <AppText weight="900" size={19} color={band.ink} style={[LTR, { lineHeight: 26 }]}>
                {data.title}
              </AppText>
            </View>
            {model ? (
              <View style={{ flexDirection: row, gap: 8 }}>
                <Stat value={n(model.tops.length)} label={t("articleStatSections")} />
                <Stat value={n(model.figures)} label={t("articleStatFigures")} />
                <Stat value={`${n(model.minutes)}′`} label={t("articleStatMinutes")} />
              </View>
            ) : null}
          </>
        ) : null}
      </View>

      {isError || !data || !model ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 24 }}>
          <AppText muted weight="600">
            {t("articleLoadError")}
          </AppText>
        </View>
      ) : (
        <ScrollView contentContainerStyle={{ padding: 12, gap: 8, paddingBottom: layout.bottomNavHeight + 24 }}>
          {summary ? (
            <Pressable
              onPress={() => read(summary.path)}
              style={{
                backgroundColor: colors.cautBg,
                borderWidth: 1,
                borderColor: colors.cautBorder,
                borderRadius: 12,
                paddingVertical: 11,
                paddingHorizontal: 12,
                gap: 2,
              }}
            >
              <AppText weight="900" size={10.5} color={colors.cautLabel} style={{ letterSpacing: 0.6 }}>
                {t("articleJumpTo")} · {summary.heading.toUpperCase()}
              </AppText>
              <AppText weight="600" size={12.5} color={colors.cautInk}>
                {t("articleJumpSub")}
              </AppText>
            </Pressable>
          ) : null}

          {model.tops.length > 0 ? (
            <View style={{ backgroundColor: colors.cardBg, borderRadius: 12, paddingVertical: 6, overflow: "hidden" }}>
              {model.tops.map((top) => {
                const open = openPath === top.path;
                const current = lastTop?.path === top.path;
                return (
                  <View key={top.path}>
                    <View
                      style={{
                        flexDirection: "row",
                        alignItems: "center",
                        backgroundColor: current ? `${colors.accent}14` : undefined,
                      }}
                    >
                      <Pressable
                        onPress={() => read(top.path)}
                        style={{ flex: 1, flexDirection: "row", alignItems: "center", gap: 10, paddingVertical: 9, paddingLeft: 12 }}
                      >
                        <AppText weight="900" size={12} color={colors.accent} style={[LTR, { width: 24 }]}>
                          {tocLabel(top.num)}
                        </AppText>
                        <AppText
                          weight={current ? "800" : "700"}
                          size={13.5}
                          color={current ? colors.accent : colors.ink}
                          style={[LTR, { flex: 1, lineHeight: 20 }]}
                        >
                          {top.heading}
                        </AppText>
                        <AppText muted size={11} style={LTR}>
                          {top.minutes}′
                        </AppText>
                      </Pressable>
                      {top.children.length > 0 ? (
                        <Pressable
                          onPress={() => setExpanded(open ? "" : top.path)}
                          hitSlop={6}
                          accessibilityLabel="expand"
                          style={{ width: 36, alignItems: "center", paddingVertical: 9 }}
                        >
                          <AppText weight="800" size={11} color={open ? colors.accent : colors.muted}>
                            {open ? "▴" : "▾"}
                          </AppText>
                        </Pressable>
                      ) : (
                        <View style={{ width: 36 }} />
                      )}
                    </View>
                    {open && top.children.length > 0 ? (
                      <View style={{ paddingLeft: 46, paddingRight: 12, paddingTop: 4, paddingBottom: 8, gap: 2 }}>
                        {top.children.map((child) => (
                          <Pressable key={child.path} onPress={() => read(child.path)} style={{ paddingVertical: 4 }}>
                            <AppText weight="600" size={12.5} color={colors.proseInk} style={[LTR, { lineHeight: 19 }]}>
                              {child.num ? `${child.num}  ` : ""}
                              {child.heading}
                            </AppText>
                          </Pressable>
                        ))}
                      </View>
                    ) : null}
                  </View>
                );
              })}
            </View>
          ) : null}

          <Pressable
            onPress={() => read(lastTop?.path)}
            style={{ height: 46, borderRadius: 12, backgroundColor: colors.accent, alignItems: "center", justifyContent: "center" }}
          >
            <AppText weight="800" size={14} color={colors.onAccent}>
              {lastTop && lastTop !== model.tops[0] && lastTop.num
                ? `${t("articleContinueFrom")} ${n(lastTop.num)}`
                : t("articleStartReading")}
            </AppText>
          </Pressable>
        </ScrollView>
      )}
    </View>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  const band = useBandColors();
  return (
    <View style={{ flex: 1, backgroundColor: band.chip, borderRadius: 10, paddingVertical: 8, paddingHorizontal: 10 }}>
      <AppText weight="900" size={17} color={band.ink} style={{ lineHeight: 24 }}>
        {value}
      </AppText>
      <AppText weight="700" size={10.5} color={band.sub} style={{ lineHeight: 16 }}>
        {label}
      </AppText>
    </View>
  );
}
