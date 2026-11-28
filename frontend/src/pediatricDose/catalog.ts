import type { CalculatorCategoryRef, CalculatorListItem } from "@/api/types";

export const PEDIATRIC_DOSE_SLUG = "pediatric-dose";
export const PEDIATRIC_DOSE_NAME = "Pediatric Dose Adjustment";
export const PEDIATRIC_DOSE_NAME_FA = "تنظیم دوز اطفال";

/** This dedicated tool has a different engine from snapshot formulas.
 * Join it to the real Pediatrics domain, independent of local database IDs.
 * Negative IDs exist only in the client catalog and are never posted to API. */
export function includePediatricDose(items: CalculatorListItem[], categories: CalculatorCategoryRef[]) {
  const root = categories.find(c => c.is_main_category && c.name.trim().toLowerCase() === "pediatrics") ?? {
    id: -200001, name: "Pediatrics", name_fa: "کودکان", parent_id: null, is_main_category: true,
  };
  const section: CalculatorCategoryRef = {
    id: -200002, name: PEDIATRIC_DOSE_NAME, name_fa: PEDIATRIC_DOSE_NAME_FA,
    parent_id: root.id, is_main_category: false,
  };
  return {
    categories: [...categories.filter(c => c.id !== section.id && c.id !== root.id), root, section],
    items: [...items.filter(c => c.slug !== PEDIATRIC_DOSE_SLUG), {
      slug: PEDIATRIC_DOSE_SLUG, name: PEDIATRIC_DOSE_NAME, name_fa: PEDIATRIC_DOSE_NAME_FA,
      description: "Pediatric dosing by age, weight, indication and preparation · UpToDate",
      description_fa: "تنظیم دوز بر اساس سن، وزن، اندیکاسیون و فرآورده · UpToDate",
      categories: [section],
    }],
  };
}
