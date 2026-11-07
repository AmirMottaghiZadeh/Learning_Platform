import type { LexicompInteraction } from "@/api/types";

export type InteractionGroup = {
  key: string;
  names: [string, string];
  severity: string;
  interactions: LexicompInteraction[];
};

const severityRank = (value: string) => ({ major: 0, moderate: 1, minor: 2 }[value.toLowerCase()] ?? 99);

/** One unordered drug pair, with every distinct source monograph preserved. */
export function groupInteractions(rows: LexicompInteraction[]): InteractionGroup[] {
  const groups = new Map<string, InteractionGroup>();
  const seen = new Set<string>();
  for (const row of rows) {
    const forward = row.object_generic_id <= row.precipitant_generic_id;
    const ids = [row.object_generic_id, row.precipitant_generic_id].sort((a, b) => a - b);
    const key = ids.join(":");
    const identity = `${key}:${row.monograph_id}`;
    if (seen.has(identity)) continue;
    seen.add(identity);
    let group = groups.get(key);
    if (!group) {
      group = { key, names: forward ? [row.object_name, row.precipitant_name] : [row.precipitant_name, row.object_name], severity: row.severity, interactions: [] };
      groups.set(key, group);
    }
    group.interactions.push(row);
    if (severityRank(row.severity) < severityRank(group.severity)) group.severity = row.severity;
  }
  for (const group of groups.values()) group.interactions.sort((a, b) => severityRank(a.severity) - severityRank(b.severity));
  return [...groups.values()].sort((a, b) => severityRank(a.severity) - severityRank(b.severity));
}
