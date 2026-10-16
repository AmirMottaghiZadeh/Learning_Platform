import { CalculatorDetail, CalculatorQuestion } from "@/api/types";
import { CalculatorAnswers } from "@/utils/calculatorEngine";
import { ModelInfo } from "@/utils/calculatorModel";

/** What every way of asking the questions is given by the calculator screen. */
export interface FlowProps {
  data: CalculatorDetail;
  info: ModelInfo;
  answers: CalculatorAnswers;
  choiceIndexes: Record<number, number>;
  unitIndexes: Record<number, number>;
  step: number;
  setStep: (update: (step: number) => number) => void;
  setAnswer: (position: number, value: number | undefined) => void;
  choose: (position: number, index: number, value: number | undefined) => void;
  setUnit: (position: number, index: number) => void;
  validate: (question: CalculatorQuestion, value: number | undefined) => string | null;
  error: string | null;
  setError: (error: string | null) => void;
  compute: () => void;
}
