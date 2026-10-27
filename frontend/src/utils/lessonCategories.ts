import { LessonGroup } from "@/api/types";

export type LessonCategory = {
  code: string;
  name_fa: string;
  name_en: string;
  topics: LessonGroup[];
};

/** The API already lists topics in category-clustered order (see
 * apps.lessons.data.study_topics), so a stable first-seen grouping here needs
 * no separate categories request. Shared by the lessons list and the study
 * plan's topic picker. */
export function groupByCategory(groups: LessonGroup[]): LessonCategory[] {
  const byCode = new Map<string, LessonCategory>();
  for (const group of groups) {
    let category = byCode.get(group.category_code);
    if (!category) {
      category = {
        code: group.category_code,
        name_fa: group.category_name_fa,
        name_en: group.category_name_en,
        topics: [],
      };
      byCode.set(group.category_code, category);
    }
    category.topics.push(group);
  }
  return [...byCode.values()];
}
