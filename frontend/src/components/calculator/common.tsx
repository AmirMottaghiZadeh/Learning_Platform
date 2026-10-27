import React from "react";
import { Pressable, View, ViewStyle } from "react-native";

import { CalculatorAnswers, ComputedResult, ResultRange, ScoreBand } from "@/utils/calculatorEngine";
import { CalculatorDetail, SectionTone } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";
import { toneColors } from "@/theme/tone";
import { ModelInfo, resultText, valueKind } from "@/utils/calculatorModel";
import { Severity, severityLevels, severityOfText } from "@/utils/severity";
import { ltrNumbers } from "@/utils/html";
import { choiceLabels } from "@/utils/calculatorLabels";

/** What every result layout receives. `results` are the ones that have an
 * answer to show, in the calculator's own order. */
export interface ResultProps {
  data: CalculatorDetail;
  info: ModelInfo;
  results: ComputedResult[];
  ranges: Map<number, ResultRange>;
  answers: CalculatorAnswers;
  /** The same results answered in the other unit system, when the
   * calculator's formulas have one. */
  altResults: ComputedResult[] | null;
  /** What the learner entered, as it was typed (see describeInputs). */
  inputs: { label: string; value: string }[];
}

/** `ok` through `deny` are four steps of seriousness (green, amber, orange,
 * red); `info` is no signal at all. */
export type Tone = "ok" | "caution" | "warn" | "deny" | "info";

const LEVEL_TONES: Tone[] = ["ok", "caution", "warn", "deny"];

export function toneOfLevel(level: Severity): Tone {
  return LEVEL_TONES[level];
}

/** The theme's colours for a tone. The app has no orange, so `warn` is made
 * here, next to the accent green, the amber and the red it sits between. */
export function useToneStyle() {
  const { colors, isDark } = useTheme();
  return (tone: Tone): { bg: string; border: string; label: string } => {
    if (tone === "ok") return { bg: `${colors.accent}14`, border: `${colors.accent}55`, label: colors.accent };
    if (tone === "info") return { bg: "transparent", border: "transparent", label: colors.accent };
    if (tone === "warn") {
      return isDark
        ? { bg: "#221812", border: "#4A3022", label: "#F2A06B" }
        : { bg: "#FFF3EA", border: "#F0C9AE", label: "#C2561A" };
    }
    return toneColors((tone === "deny" ? "deny" : "caution") as SectionTone, colors);
  };
}

/** Tone of a piece of English text, from what its words say. */
export function toneOf(text: string): Tone {
  const level = severityOfText(text);
  return level === null ? "info" : toneOfLevel(level);
}

/** The tone of each tier of a ladder given lowest-first. */
export function tiersTones(texts: string[]): Tone[] {
  return severityLevels(texts).map(toneOfLevel);
}

export function useShown() {
  const { isFa } = useLang();
  return (r: ComputedResult) => ({
    title: (isFa ? r.titleFa : r.title) || r.title,
    text: resultText(isFa ? r.answerTextFa ?? r.answerText : r.answerText),
    en: resultText(r.answerText),
  });
}

/** A line of text that must read left to right (a number with its unit)
 * whatever the language of the screen is. */
export function Ltr({
  children,
  size = 14,
  weight = "700",
  color,
  muted,
  style,
}: {
  children: React.ReactNode;
  size?: number;
  weight?: "400" | "500" | "600" | "700" | "800" | "900";
  color?: string;
  muted?: boolean;
  style?: object;
}) {
  return (
    <AppText weight={weight} size={size} color={color} muted={muted} style={{ writingDirection: "ltr", textAlign: "left", ...style }}>
      {children}
    </AppText>
  );
}

/** Result text as shown: Persian text keeps its numbers and units left to right. */
export function useDisplayText() {
  const { isFa } = useLang();
  return (text: string) => (isFa ? ltrNumbers(text) : text);
}

export function ResultCard({
  title,
  tone = "info",
  center = false,
  children,
  style,
}: {
  title?: string;
  tone?: Tone;
  /** Centre the title (for results whose headline is centred). */
  center?: boolean;
  children: React.ReactNode;
  style?: ViewStyle;
}) {
  const toneStyle = useToneStyle();
  const { isFa } = useLang();
  const t = toneStyle(tone);
  const tinted = tone !== "info";
  return (
    <Card style={{ gap: 10, ...(tinted ? { backgroundColor: t.bg, borderColor: t.border } : null), ...style }}>
      {title ? (
        <AppText weight="800" size={13} center={center} style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
          {title}
        </AppText>
      ) : null}
      {children}
    </Card>
  );
}

export function Chip({ text, tone = "info" }: { text: string; tone?: Tone }) {
  const { colors } = useTheme();
  const toneStyle = useToneStyle();
  const display = useDisplayText();
  const t = toneStyle(tone);
  return (
    <View
      style={{
        alignSelf: "flex-start",
        paddingHorizontal: 12,
        paddingVertical: 3,
        borderRadius: 999,
        borderWidth: 1,
        borderColor: tone === "info" ? colors.border : t.border,
        backgroundColor: tone === "info" ? colors.softBg : t.bg,
      }}
    >
      <AppText weight="800" size={12} color={tone === "info" ? colors.ink : t.label}>
        {display(text)}
      </AppText>
    </View>
  );
}

const hasPersian = (text: string) => /[\u0600-\u06EF\u06FA-\u06FF]/.test(text);

/** Label on one side, value on the other, with a hairline above each row but
 * the first. Values read left to right. */
export function Rows({ rows }: { rows: { label: string; value: string }[] }) {
  const { colors } = useTheme();
  const { row } = useLang();
  const display = useDisplayText();
  return (
    <View>
      {rows.map((r, i) => (
        <View
          key={`${r.label}-${i}`}
          style={{
            flexDirection: row,
            justifyContent: "space-between",
            alignItems: "baseline",
            gap: spacing.md,
            paddingVertical: 7,
            borderTopWidth: i === 0 ? 0 : 1,
            borderTopColor: colors.border,
          }}
        >
          <AppText weight="600" size={12.5} muted style={{ flexShrink: 1 }}>
            {r.label}
          </AppText>
          <AppText
            weight="800"
            size={13}
            style={{ writingDirection: hasPersian(r.value) ? "rtl" : "ltr", textAlign: "left", flexShrink: 1 }}
          >
            {display(r.value)}
          </AppText>
        </View>
      ))}
    </View>
  );
}

const plain = (text: string) => resultText(text).replace(/\s+/g, " ").toLowerCase();

/** The band a value is in. Neighbouring bands of a whole-number score share
 * their edge (BISAP: 0 to 0 and 0 to 1), so a score on that edge is in both;
 * then the row the bands were read from, when its output is at hand, says
 * which one it really is (its text contains that band's, echoed score aside),
 * and failing that the higher band is taken, as before. */
export function bandFor(bands: ScoreBand[], value: number, sourceText?: string | null): ScoreBand | null {
  const hits = bands.filter((b) => value >= b.from && value <= b.to);
  if (hits.length <= 1) return hits[0] ?? null;
  if (sourceText) {
    const said = plain(sourceText);
    const match = hits.find((b) => {
      const own = plain(b.text);
      return own !== "" && (said === own || said.includes(own));
    });
    if (match) return match;
  }
  return hits[hits.length - 1];
}

/** A tier's wording as shown: its markup and entities ("&lt; 16") decoded,
 * and a doubled percent sign in the source ("0.5-0.7%%") made single. */
export function tierText(band: ScoreBand, isFa: boolean): string {
  return resultText(isFa ? band.textFa || band.text : band.text).replace(/%{2,}/g, "%");
}

/** Whether the tier bar tells the learner anything. An open-ended scale (the
 * result reads an unbounded input such as age) cut in two is drawn over ends
 * made up for room, so it says no more than the tier itself does. */
export function showTierBar(range: ResultRange): boolean {
  if (range.bands.length === 0) return !range.minOpen && !range.maxOpen;
  return !((range.minOpen || range.maxOpen) && range.bands.length <= 2);
}

const HEADLINE_MAX = 32;

/** The tier a result falls in, ready to show:
 * - `headline`: a short label ("Low risk"), or a number or percentage under
 *   the title of the row it came from ("Mortality" / "0.1-0.2%"), shown
 *   large under the result's number;
 * - `callout`: a sentence or more, shown in its own box;
 * - `value`: a number or percentage from a row that has no title of its
 *   own, which means nothing on its own, so it isn't shown.
 * `source` is the row the tier was read from; a headline or callout stands
 * in for it, so the layout leaves it out of the list. */
export interface Tier {
  band: ScoreBand;
  text: string;
  tone: Tone;
  style: "headline" | "callout" | "value";
  title: string | null;
  source: number | null;
}

export function useTier(range: ResultRange | undefined, value: number | null, results: ComputedResult[]): Tier | null {
  const { isFa } = useLang();
  const shown = useShown();
  if (!range || range.bands.length === 0 || value === null) return null;
  const row = range.source !== undefined ? results.find((r) => r.position === range.source) : undefined;
  const band = bandFor(range.bands, value, row?.answerText);
  if (!band) return null;
  const text = tierText(band, isFa);
  if (!text) return null;
  const kind = valueKind(tierText(band, false));
  const numeric = kind === "num" || kind === "pct" || kind === "numunit";
  const title = row ? shown(row).title || null : null;
  const short = text.length <= HEADLINE_MAX && !text.includes("\n");
  return {
    band,
    text,
    tone: tiersTones(range.bands.map((b) => b.text))[range.bands.indexOf(band)],
    style: !short ? "callout" : numeric && !title ? "value" : "headline",
    title,
    source: row ? row.position : null,
  };
}

/** A tier's meaning that runs to a sentence or more: in its own box, tinted
 * by how serious it is, under the title of the row it came from, one
 * sentence to a line. */
export function Interpretation({ title, text, tone }: { title: string; text: string; tone: Tone }) {
  const { colors } = useTheme();
  const { isFa } = useLang();
  const toneStyle = useToneStyle();
  const t = toneStyle(tone);
  const tinted = tone !== "info";
  const lines = text.replace(/([.!?؟])\s+(?=\S)/g, "$1\n");
  return (
    <View
      style={{
        borderRadius: 12,
        borderWidth: 1,
        borderColor: tinted ? t.border : colors.border,
        backgroundColor: tinted ? t.bg : colors.softBg,
        paddingHorizontal: 12,
        paddingVertical: 10,
        gap: 6,
      }}
    >
      <AppText weight="800" size={12.5} color={tinted ? t.label : colors.ink} style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
        {title}
      </AppText>
      <RichLines text={lines} />
    </View>
  );
}

function fmt(v: number) {
  return String(Number(v.toFixed(2)));
}

/**
 * The calculator's own tiers drawn to scale on one bar, with a marker where
 * this result sits. The tier the marker is in is full strength, the others
 * dimmed; tier names go under their segment when there are few enough to
 * fit, and the cut-off numbers go under the boundaries. A range with no tiers
 * is one plain bar.
 */
export function TierBar({
  value,
  range,
  active: activeBand,
  showNames = true,
  isFa,
}: {
  value: number;
  range: Pick<ResultRange, "min" | "max" | "minOpen" | "maxOpen" | "bands">;
  /** The band to highlight when the layout already knows it (see bandFor). */
  active?: ScoreBand | null;
  showNames?: boolean;
  isFa: boolean;
}) {
  const { colors } = useTheme();
  const toneStyle = useToneStyle();
  const { min, max, bands } = range;
  const bandTones = tiersTones(bands.map((b) => b.text));
  const span = max - min || 1;
  const pct = (v: number) => `${Math.max(0, Math.min(100, ((v - min) / span) * 100))}%` as const;
  const active = activeBand ?? bandFor(bands, value);
  const names = showNames && bands.length > 0 && bands.length <= 4 && bands.every((b) => tierText(b, isFa).length <= 26);
  const boundaries = [...new Set(bands.slice(1).map((b) => b.from))].filter((v) => v > min && v < max);
  return (
    <View style={{ gap: 4, direction: "ltr" }}>
      <View style={{ height: 22, justifyContent: "flex-end" }}>
        <View style={{ height: 10, borderRadius: 5, backgroundColor: colors.trackBg, overflow: "hidden" }}>
          {bands.length === 0 ? (
            <View style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: pct(value), backgroundColor: colors.accent, borderRadius: 5 }} />
          ) : (
            bands.map((b, i) => {
              const tone = toneStyle(bandTones[i]);
              const isActive = b === active;
              return (
                <View
                  key={i}
                  style={{
                    position: "absolute",
                    top: 0,
                    bottom: 0,
                    left: pct(b.from),
                    width: `${Math.max(0.5, ((Math.min(b.to, max) - Math.max(b.from, min)) / span) * 100)}%`,
                    backgroundColor: tone.label,
                    opacity: isActive ? 1 : 0.32,
                    borderRightWidth: i < bands.length - 1 ? 2 : 0,
                    borderRightColor: colors.cardBg,
                  }}
                />
              );
            })
          )}
        </View>
        <View
          style={{
            position: "absolute",
            top: 0,
            left: pct(value),
            marginLeft: -2,
            width: 4,
            height: 22,
            borderRadius: 2,
            backgroundColor: colors.ink,
          }}
        />
      </View>
      {names ? (
        <View style={{ height: 34 }}>
          {bands.map((b, i) => {
            const left = Math.max(min, b.from);
            const right = Math.min(max, b.to);
            return (
              <View
                key={i}
                style={{
                  position: "absolute",
                  left: pct(left),
                  width: `${((right - left) / span) * 100}%`,
                  alignItems: "center",
                  paddingHorizontal: 1,
                }}
              >
                <AppText
                  weight={b === active ? "800" : "600"}
                  size={10.5}
                  center
                  muted={b !== active}
                  numberOfLines={2}
                  style={{ lineHeight: 15, writingDirection: isFa ? "rtl" : "ltr" }}
                >
                  {tierText(b, isFa).replace(/\s+/g, " ")}
                </AppText>
              </View>
            );
          })}
        </View>
      ) : null}
      <View style={{ height: 16 }}>
        {!range.minOpen ? (
          <Ltr size={10.5} muted weight="600" style={{ position: "absolute", left: 0 }}>
            {fmt(min)}
          </Ltr>
        ) : null}
        {boundaries.map((v, i) => (
          <View key={i} style={{ position: "absolute", left: pct(v), marginLeft: -22, width: 44, alignItems: "center" }}>
            <Ltr size={10.5} muted weight="600">
              {fmt(v)}
            </Ltr>
          </View>
        ))}
        {!range.maxOpen ? (
          <Ltr size={10.5} muted weight="600" style={{ position: "absolute", right: 0 }}>
            {fmt(max)}
          </Ltr>
        ) : null}
      </View>
    </View>
  );
}

/** Which of the learner's answers to list, as short label/value pairs. */
export function describeInputs(
  data: CalculatorDetail,
  answers: CalculatorAnswers,
  choiceIndexes: Record<number, number>,
  unitIndexes: Record<number, number>,
  isFa: boolean,
  strip: (s: string) => string,
  factorOf: (u: CalculatorDetail["questions"][number]["units"][number] | undefined) => number,
): { label: string; value: string }[] {
  const out: { label: string; value: string }[] = [];
  for (const q of data.questions) {
    const v = answers[q.position];
    if (v === undefined) continue;
    const label = strip(isFa && q.title_fa ? q.title_fa : q.title).replace(/[?؟]\s*$/, "");
    if (q.type === "multiple_choice") {
      const c = q.choices[choiceIndexes[q.position] ?? -1];
      if (c) out.push({ label, value: choiceLabels(c, isFa).join("\n") });
    } else if (q.type === "numeric_input") {
      const unit = q.units[unitIndexes[q.position] ?? 0] ?? q.units[0];
      const typed = Number((v / factorOf(unit)).toPrecision(8));
      out.push({ label, value: `${typed}${unit ? ` ${strip(isFa && unit.title_fa ? unit.title_fa : unit.title)}` : ""}` });
    }
  }
  return out;
}

/** A row that opens and closes its content. */
export function Collapse({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const { colors } = useTheme();
  const { row, isFa } = useLang();
  const [open, setOpen] = React.useState(defaultOpen);
  return (
    <View style={{ borderRadius: 12, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.softBg, overflow: "hidden" }}>
      <Pressable
        onPress={() => setOpen((v) => !v)}
        style={{ flexDirection: row, justifyContent: "space-between", alignItems: "center", gap: 8, paddingHorizontal: 12, paddingVertical: 9 }}
      >
        <AppText weight="800" size={12.5} style={{ flex: 1, writingDirection: isFa ? "rtl" : "ltr" }}>
          {title}
        </AppText>
        <AppText weight="700" size={11} color={colors.accent}>
          {open ? "▲" : "▼"}
        </AppText>
      </Pressable>
      {open ? <View style={{ paddingHorizontal: 12, paddingBottom: 12, gap: 6 }}>{children}</View> : null}
    </View>
  );
}

/** Text that may hold line breaks and "•" items, as paragraphs and bullets. */
export function RichLines({ text }: { text: string }) {
  const { colors } = useTheme();
  const { isFa } = useLang();
  const display = useDisplayText();
  const lines = text
    .split(/\n|•/)
    .map((l) => l.replace(/^-\s*/, "").trim())
    .filter(Boolean);
  const bulleted = text.includes("•") || lines.length > 2;
  return (
    <View style={{ gap: 5 }}>
      {lines.map((l, i) => (
        <View key={i} style={{ flexDirection: isFa ? "row-reverse" : "row", gap: 8, alignItems: "flex-start" }}>
          {bulleted ? <View style={{ width: 5, height: 5, borderRadius: 3, backgroundColor: colors.accent, marginTop: 9 }} /> : null}
          <AppText weight="600" size={12.5} style={{ flex: 1, lineHeight: 21, writingDirection: isFa ? "rtl" : "ltr" }}>
            {display(l)}
          </AppText>
        </View>
      ))}
    </View>
  );
}

interface Extra {
  title: string;
  text: string;
}

/** Whatever else a calculator reports besides its headline result: short
 * values as rows, a sentence or two as a titled paragraph, and anything long
 * folded away until asked for. */
export function Extras({ items }: { items: Extra[] }) {
  const { isFa, t } = useLang();
  const display = useDisplayText();
  const visible = items.filter((i) => i.text);
  const short = visible.filter((i) => i.text.length <= 28 && !i.text.includes("\n"));
  const medium = visible.filter((i) => !short.includes(i) && i.text.length <= 140 && i.text.split("\n").length <= 2);
  const long = visible.filter((i) => !short.includes(i) && !medium.includes(i));
  return (
    <>
      {short.length ? <Rows rows={short.map((r) => ({ label: r.title, value: r.text }))} /> : null}
      {medium.map((m, i) => (
        <View key={`m${i}`} style={{ gap: 2 }}>
          {m.title ? (
            <AppText weight="800" size={12.5} style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
              {m.title}
            </AppText>
          ) : null}
          <AppText weight="600" size={12.5} muted style={{ lineHeight: 21, writingDirection: isFa ? "rtl" : "ltr" }}>
            {display(m.text)}
          </AppText>
        </View>
      ))}
      {long.map((l, i) => (
        <Collapse key={`l${i}`} title={l.title || t("calcShowDetails")}>
          <RichLines text={l.text} />
        </Collapse>
      ))}
    </>
  );
}

/** The headline of a result, centred: the number (with its unit or "out of")
 * and, under it, the tier it falls in, large and in the colour of how serious
 * that tier is. */
export function Hero({
  value,
  unit,
  suffix,
  caption,
  label,
  tone = "info",
  size = 46,
}: {
  value?: string;
  unit?: string;
  suffix?: string;
  /** What the label answers ("Action", "Risk group"), small above it. */
  caption?: string | null;
  label?: string | null;
  tone?: Tone;
  size?: number;
}) {
  const toneStyle = useToneStyle();
  const { colors } = useTheme();
  const { isFa } = useLang();
  const display = useDisplayText();
  const color = tone === "info" ? colors.ink : toneStyle(tone).label;
  return (
    <View style={{ alignItems: "center", gap: 4 }}>
      {value ? (
        <View style={{ flexDirection: "row", alignItems: "baseline", justifyContent: "center", gap: 8, direction: "ltr", flexWrap: "wrap" }}>
          <AppText weight="900" size={size} center style={{ writingDirection: "ltr", lineHeight: Math.round(size * 1.2) }}>
            {value}
          </AppText>
          {unit ? (
            <AppText weight="700" size={16} muted style={{ writingDirection: "ltr", textAlign: "left" }}>
              {unit}
            </AppText>
          ) : null}
          {suffix ? (
            <AppText weight="700" size={14} muted>
              {suffix}
            </AppText>
          ) : null}
        </View>
      ) : null}
      {label && caption ? (
        <AppText weight="700" size={12} muted center style={{ writingDirection: isFa ? "rtl" : "ltr" }}>
          {caption}
        </AppText>
      ) : null}
      {label ? (
        <AppText weight="900" size={21} color={color} center style={{ lineHeight: 32, writingDirection: isFa ? "rtl" : "ltr" }}>
          {display(label)}
        </AppText>
      ) : null}
    </View>
  );
}

/** What a result means, under its headline: a hairline, then the extra rows
 * and paragraphs. Nothing at all when there are none. */
export function Explain({ items }: { items: { title: string; text: string }[] }) {
  const { colors } = useTheme();
  if (!items.some((i) => i.text)) return null;
  return (
    <View style={{ gap: 10, marginTop: 4 }}>
      <View style={{ height: 1, backgroundColor: colors.border }} />
      <Extras items={items} />
    </View>
  );
}
