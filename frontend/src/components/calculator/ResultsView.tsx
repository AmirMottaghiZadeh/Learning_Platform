import React from "react";

import { DateResult } from "./DateResult";
import { DoseResult } from "./DoseResult";
import { IndexResult } from "./IndexResult";
import { MeasureResult } from "./MeasureResult";
import { NarrativeResult } from "./NarrativeResult";
import { PanelResult } from "./PanelResult";
import { PlainResult } from "./PlainResult";
import { RiskResult } from "./RiskResult";
import { ScoreResult } from "./ScoreResult";
import { StagingResult } from "./StagingResult";
import { VerdictResult } from "./VerdictResult";
import { ResultProps } from "./common";

/** Picks the layout for the calculator's kind of result. */
export function ResultsView(props: ResultProps) {
  if (props.results.length === 0) return null;
  switch (props.info.model) {
    case "score":
      return <ScoreResult {...props} />;
    case "risk":
      return <RiskResult {...props} />;
    case "index":
      return <IndexResult {...props} />;
    case "measure":
      return <MeasureResult {...props} />;
    case "verdict":
      return <VerdictResult {...props} />;
    case "narrative":
      return <NarrativeResult {...props} />;
    case "panel":
      return <PanelResult {...props} />;
    case "dose":
      return <DoseResult {...props} />;
    case "staging":
      return <StagingResult {...props} />;
    case "date":
      return <DateResult {...props} />;
    default:
      return <PlainResult {...props} />;
  }
}
