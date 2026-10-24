import { CalculatorDetail } from "@/api/types";
import { ModelInfo } from "@/utils/calculatorModel";

/** How a calculator's questions are put to the learner:
 * - `list`: every question on one page (a long calculator, over 10 questions);
 * - `live`: one question per step with the score so far on top (scores);
 * - `cards`: one question per step. */
export type FlowLayout = "list" | "live" | "cards";

export const LIST_FROM = 11;

export function flowLayout(data: Pick<CalculatorDetail, "questions">, info: ModelInfo): FlowLayout {
  if (data.questions.length >= LIST_FROM) return "list";
  if (info.model === "score") return "live";
  return "cards";
}
