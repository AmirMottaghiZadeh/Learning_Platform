import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useMemo, useRef, useState } from "react";
import { NativeScrollEvent, NativeSyntheticEvent, Pressable, ScrollView, TextInput, View } from "react-native";

import { lessonsApi } from "@/api/endpoints";
import { LessonSection } from "@/api/types";
import { ChromeButton, LangToggleButton } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { fontFamily } from "@/theme/fonts";
import { toneColors } from "@/theme/tone";
import { useNavClearance } from "@/components/BottomNav";
import { useBleedTop } from "@/components/AppShell";

// The upstream summaries are already structured plain text -- lines starting
// "- " are a bullet list (true for 10 of the 12 clinical fields, e.g. dose,
// contraindications, adverse reactions), and a line often opens with a short
// "label: " before its content (e.g. "مکانیسم اثر: ...", "شایع: ...",
// "نادر: ..."). This recovers both instead of inventing structure the source
// doesn't have.
//
// One bullet often carries several such "issue: ..." items run together
// ("... ۲۰۰ میلی‌گرم دو بار در روز. نارسایی متوسط تا شدید کبدی: منع مصرف
// دارد."). Each issue after the first starts its own line -- inside the same
// bullet, so it reads as one item rather than a new paragraph.
//
// The two fields that are *not* bulleted (mechanism, and most of pregnancy)
// are each one dense, unbroken paragraph; each sentence becomes its own line
// there, again within the one block.
type LessonLine = { label: string | null; text: string };
type LessonBlock = { kind: "bullet" | "paragraph"; lines: LessonLine[] };

// A label is a short, word-based "issue" name immediately followed by a
// colon and its content ("نارسایی خفیف کبدی (کلاس A چایلد-پیو): ..."). Its
// own words run up to 80 characters -- real issue names do ("نارسایی متوسط
// کلیوی ...") and past that what precedes a colon is a whole sentence -- not
// counting a trailing parenthetical qualifier, which can be long ("Chronic
// P-glycoprotein inducers (rifampicin, carbamazepine, ..., St. John's
// wort)"). A standalone number outside parentheses means it's a dose line,
// not a label ("Take 2 tablets: ..."); a digit inside a word ("CYP3A") or a
// parenthesis is fine.
const LABEL_SPLIT = /^([^:：]+)[:：]\s+(.+)$/s;
const MAX_LABEL_WORDS = 80;
const MAX_LABEL_TOTAL = 200;

function parenDepth(text: string): number {
  let depth = 0;
  for (const ch of text) {
    if (ch === "(") depth++;
    else if (ch === ")" && depth > 0) depth--;
  }
  return depth;
}

function splitLabel(line: string): LessonLine {
  const m = line.match(LABEL_SPLIT);
  if (!m) return { label: null, text: line };
  const label = m[1].trim();
  const words = label.replace(/\([^()]*\)/g, " ").trim();
  const isLabel =
    words.length > 0 &&
    words.length <= MAX_LABEL_WORDS &&
    label.length <= MAX_LABEL_TOTAL &&
    parenDepth(label) === 0 &&
    !/(^|\s)\d/.test(words);
  return isLabel ? { label, text: m[2].trim() } : { label: null, text: line };
}

// The whitespace after a sentence end that's followed by a new "issue:"
// label -- the point where a run-together bullet gets a line break.
const ISSUE_BREAK = /(?<=[.!?؟])\s+(?=[^.!?؟:：\n\d]{2,80}[:：]\s)/;

// A period inside parentheses is an abbreviation ("(e.g. ...)", "(... St.
// John's wort)"), not the end of a sentence: a piece that leaves a "(" open
// is joined with the next one, so the line break -- and a label's bold --
// never cuts through a parenthesis.
function joinOpenParens(pieces: string[]): string[] {
  const out: string[] = [];
  for (const piece of pieces) {
    const prev = out[out.length - 1];
    if (prev !== undefined && parenDepth(prev) > 0) out[out.length - 1] = `${prev} ${piece}`;
    else out.push(piece);
  }
  return out;
}

// Splits after a sentence-ending mark only when it's followed by whitespace
// (and then more text) -- a decimal like "0.4" never has a space right
// after its period, so it's never mistaken for a sentence break.
function splitSentences(text: string): string[] {
  return joinOpenParens(
    text
      .split(/(?<=[.!?؟])\s+(?=\S)/)
      .map((s) => s.trim())
      .filter(Boolean),
  );
}

function splitIssues(text: string): string[] {
  return joinOpenParens(
    text
      .split(ISSUE_BREAK)
      .map((s) => s.trim())
      .filter(Boolean),
  );
}

function parseLessonText(text: string): LessonBlock[] {
  const blocks: LessonBlock[] = [];
  let paraLines: string[] = [];
  const flushParagraph = () => {
    if (paraLines.length === 0) return;
    const body = paraLines.join(" ");
    const sentences = splitSentences(body);
    blocks.push({ kind: "paragraph", lines: (sentences.length > 0 ? sentences : [body]).map(splitLabel) });
    paraLines = [];
  };
  // The source occasionally splits one bullet across two at a period inside
  // parentheses ("- ... St" / "- John's Wort): ..."): a bullet left with an
  // open "(" takes the next one in.
  let openBullet: { block: LessonBlock; raw: string } | null = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const bullet = line.match(/^-\s+(.*)$/);
    if (bullet) {
      flushParagraph();
      if (openBullet && parenDepth(openBullet.raw) > 0) {
        openBullet.raw = `${openBullet.raw} ${bullet[1]}`;
        openBullet.block.lines = splitIssues(openBullet.raw).map(splitLabel);
        continue;
      }
      const block: LessonBlock = { kind: "bullet", lines: splitIssues(bullet[1]).map(splitLabel) };
      blocks.push(block);
      openBullet = { block, raw: bullet[1] };
    } else {
      openBullet = null;
      paraLines.push(line);
    }
  }
  flushParagraph();
  return blocks;
}

function LessonBody({ text, color }: { text: string; color: string }) {
  const { colors } = useTheme();
  const { row } = useLang();
  const blocks = useMemo(() => parseLessonText(text), [text]);

  return (
    <View style={{ gap: 10 }}>
      {blocks.map((b, i) => {
        const isBullet = b.kind === "bullet";
        const size = isBullet ? 14.5 : 15;
        // Every line of a block lives in one text node, separated by "\n":
        // a new line, never the gap between blocks.
        const body = (
          <AppText
            size={size}
            weight="500"
            color={color}
            style={{ flex: isBullet ? 1 : undefined, lineHeight: isBullet ? 24 : 28 }}
          >
            {b.lines.map((line, j) => (
              <React.Fragment key={j}>
                {j > 0 ? "\n" : null}
                {line.label ? (
                  <AppText weight="800" size={size} color={colors.ink}>
                    {line.label}:{" "}
                  </AppText>
                ) : null}
                {line.text}
              </React.Fragment>
            ))}
          </AppText>
        );
        if (!isBullet) return <React.Fragment key={i}>{body}</React.Fragment>;
        return (
          <View key={i} style={{ flexDirection: row, gap: 8 }}>
            <AppText weight="700" size={size} color={colors.accent}>
              •
            </AppText>
            {body}
          </View>
        );
      })}
    </View>
  );
}

/** A section's text in the current language -- or, if this section was only
 * summarised in the other one, that text rather than an empty card. */
function sectionText(b: LessonSection, isFa: boolean): string {
  return (isFa ? b.text_fa : b.text_en) || (isFa ? b.text_en : b.text_fa);
}

export function LessonDetailScreen() {
  const navClearance = useNavClearance();
  const bleedTop = useBleedTop(true);
  const { isFa, n, row } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const navigate = useNav((s) => s.navigate);
  const code = String(useNav((s) => s.params.code ?? ""));
  const slug = String(useNav((s) => s.params.slug ?? ""));
  const queryClient = useQueryClient();

  const [progressPct, setProgressPct] = useState(4);
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState("");
  const marked = useRef(false);

  // The chapter (names only, usually already cached by the list screen) is
  // just for the header; the lesson itself is this one drug's own fetch.
  const { data } = useQuery({
    queryKey: ["chapter", code],
    queryFn: () => lessonsApi.chapter(code),
    enabled: !!code,
  });
  const drugSlug = slug || data?.drugs[0]?.slug || "";
  const { data: drug, isLoading } = useQuery({
    queryKey: ["lesson-drug", drugSlug],
    queryFn: () => lessonsApi.drug(drugSlug),
    enabled: !!drugSlug,
  });

  const markRead = useMutation({
    mutationFn: () => lessonsApi.saveProgress(code, { drug_slug: drugSlug, scroll_pct: 100 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chapter", code] });
      queryClient.invalidateQueries({ queryKey: ["lesson-groups"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const blocks: LessonSection[] = useMemo(() => {
    const list = drug?.lesson_sections ?? [];
    const q = query.trim().toLowerCase();
    if (!q) return list;
    return list.filter(
      (b) =>
        (isFa ? b.title_fa : b.title_en).toLowerCase().includes(q) ||
        sectionText(b, isFa).toLowerCase().includes(q),
    );
  }, [drug, query, isFa]);

  const onScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const { contentOffset, contentSize, layoutMeasurement } = e.nativeEvent;
    const max = contentSize.height - layoutMeasurement.height;
    const pct = max > 0 ? Math.min(100, Math.round((contentOffset.y / max) * 100)) : 100;
    setProgressPct(Math.max(4, pct));
    if (pct > 92 && !marked.current && drugSlug) {
      marked.current = true;
      markRead.mutate();
    }
  };

  if (isLoading || !drugSlug) return <LoadingState />;

  const hasBoxed = (drug?.sections ?? []).some((s) => s.field === "boxed_warning" && s.has_summary);
  const hasAbuse = (drug?.sections ?? []).some((s) => s.field === "abuse" && s.has_summary);
  const mins = Math.max(
    3,
    Math.round((drug?.lesson_sections.reduce((a, b) => a + sectionText(b, isFa).length, 0) ?? 0) / 620),
  );

  return (
    <View style={{ flex: 1, backgroundColor: colors.cardBg }}>
      <View style={{ paddingHorizontal: 20, paddingTop: 18 + bleedTop }}>
        <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
          <View style={{ flexDirection: row, alignItems: "center", gap: 10 }}>
            <ChromeButton onPress={goBack} size={30}>
              <AppText weight="800" size={15} color={colors.ink}>
                {isFa ? "›" : "‹"}
              </AppText>
            </ChromeButton>
            <AppText weight="800" size={12} muted>
              {data ? (isFa ? data.name_fa : data.name_en) : code}
            </AppText>
          </View>
          <View style={{ flexDirection: row, alignItems: "center", gap: 8 }}>
            <ChromeButton onPress={() => setSearchOpen((v) => !v)} size={30}>
              <AppText size={14} color={colors.muted}>
                ⌕
              </AppText>
            </ChromeButton>
            <LangToggleButton />
          </View>
        </View>

        <View style={{ height: 3, backgroundColor: colors.trackBg, borderRadius: 2, marginTop: 13 }}>
          <View style={{ width: `${progressPct}%`, height: 3, backgroundColor: colors.accent, borderRadius: 2 }} />
        </View>

        {searchOpen ? (
          <View
            style={{
              flexDirection: row,
              alignItems: "center",
              gap: 9,
              backgroundColor: colors.softBg,
              borderWidth: 1,
              borderColor: colors.trackBg,
              borderRadius: 13,
              paddingHorizontal: 12,
              paddingVertical: 8,
              marginTop: 12,
            }}
          >
            <AppText muted>⌕</AppText>
            <TextInput
              value={query}
              onChangeText={setQuery}
              placeholder={isFa ? "جست‌وجو در فصل…" : "Search this chapter…"}
              placeholderTextColor={colors.muted}
              autoFocus
              style={{
                flex: 1,
                fontFamily: fontFamily("600"),
                fontSize: 13,
                color: colors.ink,
                textAlign: isFa ? "right" : "left",
                padding: 0,
              }}
            />
          </View>
        ) : null}
      </View>

      <ScrollView
        style={{ flex: 1 }}
        onScroll={onScroll}
        scrollEventThrottle={64}
        contentContainerStyle={{
          paddingHorizontal: 22,
          paddingTop: 20,
          paddingBottom: navClearance + 24,
        }}
        showsVerticalScrollIndicator={false}
      >
        <AppText weight="900" size={26} style={{ lineHeight: 38 }}>
          {drug?.name}
        </AppText>
        <AppText weight="700" size={13} muted style={{ marginTop: 4 }}>
          {[...(drug?.pharm_classes ?? []), ...(drug?.atc_codes ?? []).map((a) => a.code)].join(" · ")}
        </AppText>

        <View style={{ flexDirection: row, flexWrap: "wrap", gap: 6, marginTop: 13 }}>
          {hasBoxed ? (
            <Badge bg={colors.boxedBorder} fg={colors.cardBg} text={isFa ? "جعبه‌سیاه" : "Boxed"} />
          ) : null}
          {hasAbuse ? (
            <Badge bg={colors.specBg} fg={colors.specLabel} text={isFa ? "کنترل‌شده" : "Controlled"} border={colors.specBorder} />
          ) : null}
          <Badge
            bg={colors.softBg}
            fg={colors.muted}
            border={colors.trackBg}
            text={isFa ? `${n(mins)} دقیقه` : `${mins} min`}
          />
        </View>

        {blocks.length === 0 ? (
          <AppText muted weight="600" size={13} style={{ marginTop: 24 }}>
            {isFa ? "چیزی پیدا نشد." : "Nothing found."}
          </AppText>
        ) : (
          blocks.map((b) => {
            const tc = toneColors(b.tone, colors);
            const isBox = b.tone !== "info";
            return (
              <View
                key={b.key}
                style={[
                  { marginTop: 20 },
                  isBox && {
                    backgroundColor: tc.bg,
                    borderWidth: 1,
                    borderColor: tc.border,
                    borderRadius: 14,
                    padding: 14,
                  },
                ]}
              >
                <AppText weight="900" size={isBox ? 14 : 18} color={isBox ? tc.label : colors.ink}>
                  {isFa ? b.title_fa : b.title_en}
                </AppText>
                <View style={{ marginTop: 10 }}>
                  <LessonBody text={sectionText(b, isFa)} color={colors.proseInk} />
                </View>
              </View>
            );
          })
        )}

        <Pressable
          onPress={() => drug && navigate("quiz", { ingredientSlug: drug.slug })}
          style={{
            marginTop: 28,
            backgroundColor: colors.accent + "12",
            borderWidth: 1,
            borderColor: colors.trackBg,
            borderRadius: 16,
            padding: 16,
          }}
        >
          <AppText weight="800" size={14}>
            {isFa ? `خودآزمایی ${drug?.name ?? ""}` : `Self-test: ${drug?.name ?? ""}`}
          </AppText>
          <AppText muted weight="600" size={12} style={{ marginTop: 4 }}>
            {isFa
              ? "بر اساس اندیکاسیون، عوارض جانبی، هشدار، منع مطلق و دوز همین دارو"
              : "Covers this drug's indications, adverse reactions, warnings, contraindications and dosing"}
          </AppText>
          <AppText weight="900" size={13} color={colors.accent} style={{ marginTop: 10 }}>
            {isFa ? "شروع آزمون ‹" : "Start quiz ›"}
          </AppText>
        </Pressable>
      </ScrollView>
    </View>
  );
}

function Badge({ bg, fg, text, border }: { bg: string; fg: string; text: string; border?: string }) {
  return (
    <View
      style={{
        backgroundColor: bg,
        borderWidth: border ? 1 : 0,
        borderColor: border,
        borderRadius: 8,
        paddingHorizontal: 10,
        paddingVertical: 5,
      }}
    >
      <AppText weight="900" size={11} color={fg}>
        {text}
      </AppText>
    </View>
  );
}
