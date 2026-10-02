import { CalculatorListItem } from "@/api/types";

export interface CalculatorCategory {
  name: string;
  calculators: CalculatorListItem[];
}

/** A calculator is cross-listed under every clinical category it belongs to
 * (the source data already models it that way, e.g. a pediatric screener
 * sitting under both "Pediatrics" and "Mental Health") -- so it legitimately
 * appears more than once across the grouped result. */
export function groupByCategory(items: CalculatorListItem[]): CalculatorCategory[] {
  const byName = new Map<string, CalculatorListItem[]>();
  for (const item of items) {
    const categories = item.categories.length ? item.categories : ["Other"];
    for (const name of categories) {
      const list = byName.get(name);
      if (list) list.push(item);
      else byName.set(name, [item]);
    }
  }
  return [...byName.entries()]
    .map(([name, calculators]) => ({ name, calculators }))
    .sort((a, b) => a.name.localeCompare(b.name));
}
