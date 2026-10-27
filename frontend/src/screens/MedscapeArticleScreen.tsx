import { useQuery } from "@tanstack/react-query";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Image,
  LayoutChangeEvent,
  Modal,
  NativeScrollEvent,
  Platform,
  NativeSyntheticEvent,
  Pressable,
  ScrollView,
  TextInput,
  View,
} from "react-native";
import { StatusBar } from "expo-status-bar";

import { medscapeApi } from "@/api/endpoints";
import { MedscapeBlock, MedscapeSection } from "@/api/types";
import {
  FindState,
  ListMarker,
  NumberedHeading,
  countMatches,
  highlight,
} from "@/components/article/ArticleParts";
import { BackGlyph, BandButton, useBandColors } from "@/components/article/Band";
import { MediaViewer } from "@/components/article/MediaViewer";
import { MediaContent } from "@/components/article/mediaPage";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useDebounced } from "@/hooks/useDebounced";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";
import { useNav } from "@/store/nav";
import { useReader, useReaderScale } from "@/store/reader";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { layout } from "@/theme/tokens";
import { buildMedscapeModel, referencesTop } from "@/utils/medscapeArticle";
import { useNavClearance } from "@/components/BottomNav";
import { useBleedTop } from "@/components/AppShell";

const LTR = { textAlign: "left" as const, writingDirection: "ltr" as const };

type MatchIndex = {
  /** text key -> global index of its first match */
  starts: Map<string, number>;
  /** global match index -> key of the block holding it */
  owners: string[];
};

/** Every searchable text of the article, in reading order, with the key the
 * renderer gives it -- so the n-th match counted here is the n-th match
 * highlighted on screen. */
function forEachText(
  sections: MedscapeSection[],
  visit: (textKey: string, blockKey: string, text: string) => void,
  prefix = "",
) {
  sections.forEach((section, i) => {
    const path = prefix ? `${prefix}.${i}` : String(i);
    section.blocks.forEach((block, b) => {
      const blockKey = `${path}/${b}`;
      if (block.type === "paragraph") visit(blockKey, blockKey, block.text);
      else if (block.type === "list") block.items.forEach((item, k) => visit(`${blockKey}/${k}`, blockKey, item));
      else if (block.type === "table") {
        (block.headers ?? []).forEach((cell, c) => visit(`${blockKey}/h/${c}`, blockKey, cell));
        block.rows.forEach((cells, r) => cells.forEach((cell, c) => visit(`${blockKey}/${r}/${c}`, blockKey, cell)));
      }
    });
    forEachText(section.children, visit, path);
  });
}

function indexMatches(sections: MedscapeSection[], term: string): MatchIndex {
  const starts = new Map<string, number>();
  const owners: string[] = [];
  if (!term) return { starts, owners };
  forEachText(sections, (textKey, blockKey, text) => {
    const count = countMatches(text, term);
    if (!count) return;
    starts.set(textKey, owners.length);
    for (let i = 0; i < count; i++) owners.push(blockKey);
  });
  return { starts, owners };
}

type ReaderCtx = {
  numbers: Map<string, string | null>;
  find: FindState;
  starts: Map<string, number>;
  scale: number;
  registerBlock: (key: string, view: View | null) => void;
  registerSection: (path: string, view: View | null) => void;
  /** Opens an image or a table full-screen (MediaViewer). */
  openMedia: (media: MediaContent) => void;
};

const ReaderContext = React.createContext<ReaderCtx | null>(null);
const useReaderCtx = () => React.useContext(ReaderContext) as ReaderCtx;

/** A guideline/disease article in the reader (design option 3): the teal
 * band with tabs for the top-level sections, numbered headings, in-article
 * search, and a floating bar for the contents, text size and references.
 * Opened at `params.path` (a section path from the article's home page);
 * the section in view is remembered for the home page's "continue" button. */
export function MedscapeArticleScreen() {
  const navClearance = useNavClearance();
  const bleedTop = useBleedTop(true);
  const { t, n, row, isFa } = useLang();
  const { colors, isDark } = useTheme();
  const band = useBandColors();
  const goBack = useNav((s) => s.goBack);
  const slug = String(useNav((s) => s.params.slug ?? ""));
  const startPath = useNav((s) => s.params.path) as string | undefined;
  const scale = useReaderScale();
  const cycleScale = useReader((s) => s.cycleScale);
  const rememberSection = useReader((s) => s.rememberSection);

  const { data, isLoading } = useQuery({
    queryKey: ["medscape-article", slug],
    queryFn: () => medscapeApi.detail(slug),
    enabled: !!slug,
  });
  const model = useMemo(() => (data ? buildMedscapeModel(data.sections) : null), [data]);
  const references = model ? referencesTop(model) : null;

  // -- in-article search ----------------------------------------------------
  const [searchOpen, setSearchOpen] = useState(false);
  const [media, setMedia] = useState<MediaContent | null>(null);
  const [query, setQuery] = useState("");
  const term = useDebounced(query.trim().toLowerCase(), 250);
  const matches = useMemo(() => indexMatches(data?.sections ?? [], term), [data, term]);
  const [current, setCurrent] = useState(0);
  const total = matches.owners.length;
  useEffect(() => setCurrent(0), [term]);
  const find: FindState = { term, current: total ? current : -1 };

  const [tocOpen, setTocOpen] = useState(false);
  useBackInterceptor(tocOpen, () => setTocOpen(false));
  useBackInterceptor(searchOpen && !tocOpen, () => closeSearch());

  // -- positions --------------------------------------------------------------
  const scrollRef = useRef<ScrollView>(null);
  const contentRef = useRef<View>(null);
  const tabsRef = useRef<ScrollView>(null);
  const blockViews = useRef(new Map<string, View>());
  const sectionViews = useRef(new Map<string, View>());
  const topY = useRef(new Map<number, number>());
  const tabX = useRef(new Map<number, number>());
  const [active, setActive] = useState(-1);

  const registerBlock = useCallback((key: string, view: View | null) => {
    if (view) blockViews.current.set(key, view);
    else blockViews.current.delete(key);
  }, []);
  const registerSection = useCallback((path: string, view: View | null) => {
    if (view) sectionViews.current.set(path, view);
    else sectionViews.current.delete(path);
  }, []);

  const scrollToView = (view: View | undefined, offset = 12, animated = true) => {
    const content = contentRef.current;
    if (!view || !content) return;
    view.measureLayout(
      content,
      (_x, y) => scrollRef.current?.scrollTo({ y: Math.max(0, y - offset), animated }),
      () => undefined,
    );
  };
  const jumpTo = (path: string, animated = true) => scrollToView(sectionViews.current.get(path), 12, animated);

  // Open at the requested section once the article has laid out.
  const jumped = useRef(false);
  const onContentLayout = () => {
    if (jumped.current || !startPath) return;
    jumped.current = true;
    setTimeout(() => jumpTo(startPath, false), 30);
  };

  useEffect(() => {
    if (!total) return;
    scrollToView(blockViews.current.get(matches.owners[current]), 120);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current, matches]);

  const onScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    if (!model) return;
    const y = e.nativeEvent.contentOffset.y + 80;
    let next = -1;
    for (const top of model.tops) {
      const at = topY.current.get(top.index);
      if (at !== undefined && at <= y) next = top.index;
    }
    if (next !== active) {
      setActive(next);
      if (next >= 0) {
        rememberSection(`medscape:${slug}`, next);
        const x = tabX.current.get(next);
        if (x !== undefined) tabsRef.current?.scrollTo({ x: Math.max(0, x - 24), animated: true });
      }
    }
  };

  const closeSearch = () => {
    setSearchOpen(false);
    setQuery("");
  };

  if (isLoading || !data || !model) return <LoadingState />;

  // Before the first scroll report, the article's first section is the one in view.
  const activeTop = active >= 0 ? active : (model.tops[0]?.index ?? -1);

  const pillBg = isDark ? colors.trackBg : colors.ink;
  const pillInk = isDark ? colors.ink : "#FFFFFF";

  return (
    <View style={{ flex: 1, backgroundColor: colors.cardBg }}>
      <View style={{ backgroundColor: band.bg, paddingHorizontal: 16, paddingTop: 14 + bleedTop, gap: 8 }}>
        <StatusBar style="light" />
        <View style={{ flexDirection: row, alignItems: "center", gap: 10 }}>
          <BandButton onPress={goBack} label="back">
            <BackGlyph color={band.ink} />
          </BandButton>
          <AppText weight="700" size={12} color={band.sub} numberOfLines={1} center style={{ flex: 1, writingDirection: "ltr" }}>
            {data.title}
          </AppText>
          <BandButton onPress={() => (searchOpen ? closeSearch() : setSearchOpen(true))} label="search">
            <AppText weight="800" size={15} color={searchOpen ? band.eyebrow : band.ink} center style={{ lineHeight: 20 }}>
              ⌕
            </AppText>
          </BandButton>
        </View>
        <ScrollView
          ref={tabsRef}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ flexDirection: "row", gap: 2 }}
          style={{ direction: "ltr" } as object}
        >
          {model.tops.map((top) => {
            const on = top.index === activeTop;
            return (
              <Pressable
                key={top.path}
                onPress={() => jumpTo(top.path)}
                onLayout={(e: LayoutChangeEvent) => tabX.current.set(top.index, e.nativeEvent.layout.x)}
                style={{
                  paddingHorizontal: 10,
                  paddingTop: 7,
                  paddingBottom: 6,
                  borderBottomWidth: 3,
                  borderBottomColor: on ? band.eyebrow : "transparent",
                }}
              >
                <AppText weight={on ? "800" : "700"} size={12} color={on ? band.ink : band.sub} style={[LTR, { lineHeight: 18 }]}>
                  {top.num ? `${top.num} ` : ""}
                  {top.heading}
                </AppText>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>

      {searchOpen ? (
        <View
          style={{
            flexDirection: row,
            alignItems: "center",
            gap: 8,
            paddingHorizontal: 18,
            paddingVertical: 10,
            borderBottomWidth: 1,
            borderBottomColor: colors.sheetLine,
            backgroundColor: colors.softBg,
          }}
        >
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder={t("uptodateSearchInArticleHint")}
            placeholderTextColor={colors.muted}
            autoFocus
            style={{
              flex: 1,
              fontFamily: fontFamily("600"),
              fontSize: 13,
              color: colors.ink,
              textAlign: isFa ? "right" : "left",
              padding: 0,
              ...(Platform.OS === "web" ? ({ outlineStyle: "none" } as object) : null),
            }}
          />
          {term ? (
            <AppText muted weight="700" size={12}>
              {total > 0 ? `${n(current + 1)} ${t("uptodateMatchCount")} ${n(total)}` : t("uptodateNoMatches")}
            </AppText>
          ) : null}
          <Pressable onPress={() => setCurrent((c) => (c - 1 + total) % total)} disabled={!total} hitSlop={8}>
            <AppText weight="800" size={16} color={total ? colors.ink : colors.muted}>
              {isFa ? "›" : "‹"}
            </AppText>
          </Pressable>
          <Pressable onPress={() => setCurrent((c) => (c + 1) % total)} disabled={!total} hitSlop={8}>
            <AppText weight="800" size={16} color={total ? colors.ink : colors.muted}>
              {isFa ? "‹" : "›"}
            </AppText>
          </Pressable>
        </View>
      ) : null}

      <ReaderContext.Provider
        value={{ numbers: model.numbers, find, starts: matches.starts, scale, registerBlock, registerSection, openMedia: setMedia }}
      >
        <ScrollView
          ref={scrollRef}
          onScroll={onScroll}
          scrollEventThrottle={64}
          contentContainerStyle={{ paddingBottom: navClearance + 90 }}
        >
          <View ref={contentRef} onLayout={onContentLayout} style={{ paddingHorizontal: 18, paddingTop: 16, gap: 26 }}>
            {data.sections.map((section, i) => (
              <View
                key={i}
                onLayout={(e: LayoutChangeEvent) => topY.current.set(i, e.nativeEvent.layout.y)}
              >
                <SectionView section={section} path={String(i)} depth={0} />
              </View>
            ))}
          </View>
        </ScrollView>
      </ReaderContext.Provider>

      <View
        pointerEvents="box-none"
        style={{ position: "absolute", left: 0, right: 0, bottom: navClearance + 12, alignItems: "center" }}
      >
        <View style={{ flexDirection: row, gap: 4, backgroundColor: pillBg, borderRadius: 999, padding: 5 }}>
          <PillButton label={t("articleToc")} color={pillInk} onPress={() => setTocOpen(true)} />
          <PillButton label="Aa" color={pillInk} onPress={cycleScale} />
          <PillButton
            label={references ? t("articleReferences") : t("articleTop")}
            color={colors.onAccent}
            bg={colors.accent}
            onPress={() =>
              references ? jumpTo(references.path) : scrollRef.current?.scrollTo({ y: 0, animated: true })
            }
          />
        </View>
      </View>

      <Modal visible={tocOpen} transparent animationType="fade" onRequestClose={() => setTocOpen(false)}>
        <Pressable style={{ flex: 1, backgroundColor: "rgba(4,10,9,0.5)", justifyContent: "flex-end" }} onPress={() => setTocOpen(false)}>
          <Pressable
            onPress={() => undefined}
            style={{
              maxHeight: "78%",
              backgroundColor: colors.cardBg,
              borderTopLeftRadius: 22,
              borderTopRightRadius: 22,
              paddingTop: 10,
            }}
          >
            <View style={{ alignSelf: "center", width: 40, height: 4, borderRadius: 2, backgroundColor: colors.trackBg, marginBottom: 10 }} />
            <AppText weight="900" size={15} style={{ paddingHorizontal: 20, marginBottom: 6 }}>
              {t("articleContents")}
            </AppText>
            <ScrollView contentContainerStyle={{ paddingHorizontal: 12, paddingBottom: 28 }}>
              {model.headed.map((entry) => {
                const top = entry.depth === 0;
                const on = top && Number(entry.path) === activeTop;
                return (
                  <Pressable
                    key={entry.path}
                    onPress={() => {
                      setTocOpen(false);
                      setTimeout(() => jumpTo(entry.path), 60);
                    }}
                    style={{
                      paddingVertical: top ? 9 : 6,
                      paddingLeft: 8 + entry.depth * 16,
                      paddingRight: 8,
                      borderRadius: 10,
                      backgroundColor: on ? `${colors.accent}14` : undefined,
                    }}
                  >
                    <AppText
                      weight={top ? "800" : "600"}
                      size={top ? 14 : 13}
                      color={top ? (on ? colors.accent : colors.ink) : entry.depth > 1 ? colors.muted : colors.proseInk}
                      style={[LTR, { lineHeight: top ? 21 : 19 }]}
                    >
                      {entry.num ? `${entry.num}  ` : ""}
                      {entry.heading}
                    </AppText>
                  </Pressable>
                );
              })}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>

      <MediaViewer media={media} onClose={() => setMedia(null)} />
    </View>
  );
}

function PillButton({ label, color, bg, onPress }: { label: string; color: string; bg?: string; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      style={{ height: 36, paddingHorizontal: 14, borderRadius: 18, backgroundColor: bg ?? "transparent", justifyContent: "center" }}
    >
      <AppText weight="800" size={12} color={color} center style={{ lineHeight: 18 }}>
        {label}
      </AppText>
    </Pressable>
  );
}

function SectionView({ section, path, depth }: { section: MedscapeSection; path: string; depth: number }) {
  const { numbers, scale, registerSection } = useReaderCtx();
  if (!section.heading && section.blocks.length === 0 && section.children.length === 0) return null;

  const level = depth === 0 ? 1 : depth === 1 ? 2 : 3;
  const gapAfterHeading = level === 1 ? 14 : 9;

  return (
    <View>
      {section.heading ? (
        <View ref={(view) => registerSection(path, view)} style={{ marginBottom: gapAfterHeading }}>
          <NumberedHeading level={level} num={numbers.get(path) ?? null} title={section.heading} scale={scale} />
        </View>
      ) : null}
      {section.blocks.length > 0 ? (
        <View style={{ gap: 10 }}>
          {section.blocks.map((block, i) => (
            <BlockView key={i} block={block} blockKey={`${path}/${i}`} />
          ))}
        </View>
      ) : null}
      {section.children.length > 0 ? (
        <View style={{ gap: level === 1 ? 20 : 16, marginTop: section.blocks.length > 0 ? 18 : 0 }}>
          {section.children.map((child, i) => (
            <SectionView key={i} section={child} path={`${path}.${i}`} depth={depth + 1} />
          ))}
        </View>
      ) : null}
    </View>
  );
}

function BlockView({ block, blockKey }: { block: MedscapeBlock; blockKey: string }) {
  const { colors } = useTheme();
  const { find, starts, scale, registerBlock, openMedia } = useReaderCtx();
  const mark = (text: string, key: string) =>
    highlight(text, find, starts.get(key) ?? 0, `${colors.accent}33`, colors.accent, colors.onAccent);
  const ref = (view: View | null) => registerBlock(blockKey, view);

  if (block.type === "paragraph") {
    return (
      <View ref={ref}>
        <AppText weight="500" size={14 * scale} color={colors.proseInk} style={[LTR, { lineHeight: Math.round(24 * scale) }]}>
          {mark(block.text, blockKey)}
        </AppText>
      </View>
    );
  }

  if (block.type === "list") {
    const lineHeight = Math.round(22 * scale);
    return (
      <View ref={ref} style={{ gap: 7 }}>
        {block.items.map((item, i) => (
          <View key={i} style={{ flexDirection: "row", gap: 10 }}>
            {block.ordered ? (
              <AppText weight="800" size={13 * scale} color={colors.accent} style={[LTR, { lineHeight, minWidth: 16 }]}>
                {i + 1}.
              </AppText>
            ) : (
              <ListMarker lineHeight={lineHeight} />
            )}
            <AppText weight="500" size={14 * scale} color={colors.proseInk} style={[LTR, { flex: 1, lineHeight }]}>
              {mark(item, `${blockKey}/${i}`)}
            </AppText>
          </View>
        ))}
      </View>
    );
  }

  if (block.type === "table") {
    return (
      <Pressable
        ref={ref}
        onPress={() => openMedia({ kind: "table", headers: block.headers, rows: block.rows, caption: "" })}
        accessibilityRole="button"
        style={{ borderWidth: 1, borderColor: colors.trackBg, borderRadius: 12, overflow: "hidden" }}
      >
        {block.headers ? (
          <TableRow cells={block.headers.map((cell, c) => mark(cell, `${blockKey}/h/${c}`))} header />
        ) : null}
        {block.rows.map((cells, r) => (
          <TableRow key={r} cells={cells.map((cell, c) => mark(cell, `${blockKey}/${r}/${c}`))} first={r === 0 && !block.headers} />
        ))}
        <EnlargeBadge />
      </Pressable>
    );
  }

  if (block.type === "image") {
    return (
      <View ref={ref}>
        <ImageBlockView id={block.id} alt={block.alt} caption={block.caption} />
      </View>
    );
  }

  return null;
}

/** «⤢» in the corner of an image or a table: it opens full-screen. */
function EnlargeBadge() {
  const { t } = useLang();
  return (
    <View
      pointerEvents="none"
      accessibilityLabel={t("mediaEnlarge")}
      style={{
        position: "absolute",
        top: 8,
        right: 8,
        width: 28,
        height: 28,
        borderRadius: 14,
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(10,20,18,0.55)",
      }}
    >
      <AppText weight="800" size={14} color="#FFFFFF" center style={{ lineHeight: 18, writingDirection: "ltr" }}>
        ⤢
      </AppText>
    </View>
  );
}

function TableRow({ cells, header, first }: { cells: React.ReactNode[]; header?: boolean; first?: boolean }) {
  const { colors } = useTheme();
  const { scale } = useReaderCtx();
  return (
    <View
      style={{
        flexDirection: "row",
        backgroundColor: header ? colors.softBg : colors.cardBg,
        borderTopWidth: header || first ? 0 : 1,
        borderTopColor: colors.sheetLine,
      }}
    >
      {cells.map((cell, i) => (
        <View key={i} style={{ flex: 1, paddingVertical: 8, paddingHorizontal: 10 }}>
          <AppText
            weight={header ? "800" : "500"}
            size={(header ? 11.5 : 12) * scale}
            color={header ? colors.ink : colors.proseInk}
            style={[LTR, { lineHeight: Math.round(18 * scale) }]}
          >
            {cell}
          </AppText>
        </View>
      ))}
    </View>
  );
}

function ImageBlockView({ id, alt, caption }: { id: number; alt: string; caption: string }) {
  const { colors } = useTheme();
  const { openMedia } = useReaderCtx();
  const { data } = useQuery({
    queryKey: ["medscape-image", id],
    queryFn: () => medscapeApi.image(id),
  });
  const src = data ? `data:${data.content_type};base64,${data.data_base64}` : null;

  return (
    <View style={{ gap: 6 }}>
      <Pressable
        onPress={() => (src ? openMedia({ kind: "image", src, alt, caption }) : undefined)}
        disabled={!src}
        accessibilityRole="imagebutton"
        accessibilityLabel={alt}
        style={{
          height: 220,
          borderRadius: 12,
          backgroundColor: colors.softBg,
          borderWidth: 1,
          borderColor: colors.trackBg,
          overflow: "hidden",
        }}
      >
        {src ? (
          <>
            <Image source={{ uri: src }} accessibilityLabel={alt} style={{ width: "100%", height: "100%" }} resizeMode="contain" />
            <EnlargeBadge />
          </>
        ) : null}
      </Pressable>
      {caption ? (
        <AppText muted weight="600" size={11.5} style={LTR}>
          {caption}
        </AppText>
      ) : null}
    </View>
  );
}
