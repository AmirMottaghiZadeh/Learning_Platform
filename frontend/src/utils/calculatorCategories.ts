import { CalculatorCategoryRef, CalculatorListItem } from "@/api/types";

/** Groups calculators by the source snapshot's own two-level category tree
 * (main domain -> subtopic -> calculator), in both languages, instead of a
 * hand-maintained English-only reconstruction of it: `allCategories` (every
 * node, fetched once via calculatorsApi.categories()) carries the real
 * `parent_id` / `is_main_category` relationships, so grouping is a plain
 * join against each calculator's own (few) category tags rather than a
 * ~175-line guessed dictionary.
 *
 * A calculator can be tagged with a subtopic whose parent it ISN'T also
 * tagged with directly -- that subtopic still nests under its real parent
 * here, since the parent lookup goes through `allCategories` (the full
 * tree), not just the tags present on that one calculator. A main category
 * can also be tagged directly with no finer subtopic -- folded into a
 * "General" subgroup like any other, so every calculator sits at the same
 * depth (domain -> subgroup -> calculator) with nothing out of place.
 */

const GENERAL_ID = -1;

export interface CalculatorSubgroup {
  id: number;
  name: string;
  name_fa: string;
  calculators: CalculatorListItem[];
}

export interface CalculatorMainGroup {
  id: number;
  name: string;
  name_fa: string;
  subgroups: CalculatorSubgroup[];
}

export function groupByMainCategory(
  items: CalculatorListItem[],
  allCategories: CalculatorCategoryRef[],
): CalculatorMainGroup[] {
  const categoryById = new Map(allCategories.map((c) => [c.id, c]));

  type MainAcc = { ref: CalculatorCategoryRef; subgroups: Map<number, { ref: CalculatorCategoryRef | null; calculators: CalculatorListItem[] }> };
  const mains = new Map<number, MainAcc>();

  const ensureMain = (ref: CalculatorCategoryRef) => {
    let m = mains.get(ref.id);
    if (!m) {
      m = { ref, subgroups: new Map() };
      mains.set(ref.id, m);
    }
    return m;
  };
  const push = (main: MainAcc, subId: number, subRef: CalculatorCategoryRef | null, item: CalculatorListItem) => {
    let sub = main.subgroups.get(subId);
    if (!sub) {
      sub = { ref: subRef, calculators: [] };
      main.subgroups.set(subId, sub);
    }
    sub.calculators.push(item);
  };

  for (const item of items) {
    for (const tag of item.categories) {
      if (tag.is_main_category) {
        push(ensureMain(tag), GENERAL_ID, null, item);
        continue;
      }
      const parent = tag.parent_id != null ? categoryById.get(tag.parent_id) : undefined;
      if (!parent) continue; // orphaned tag with no known main ancestor -- drop rather than invent a home
      push(ensureMain(parent), tag.id, tag, item);
    }
  }

  return [...mains.values()]
    .map((main) => ({
      id: main.ref.id,
      name: main.ref.name,
      name_fa: main.ref.name_fa,
      subgroups: [...main.subgroups.entries()]
        .map(([subId, sub]) => ({
          id: subId,
          name: sub.ref?.name ?? "General",
          name_fa: sub.ref?.name_fa ?? "عمومی",
          calculators: sub.calculators,
        }))
        .sort((a, b) => (a.id === GENERAL_ID ? 1 : b.id === GENERAL_ID ? -1 : a.name.localeCompare(b.name))),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
}
