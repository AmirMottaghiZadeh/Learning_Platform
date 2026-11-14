import React from "react";

import { CardsFlow } from "./CardsFlow";
import { ChecklistFlow } from "./ChecklistFlow";
import { flowLayout } from "./layout";
import { FlowProps } from "./types";

/** Asks the calculator's questions in the layout that suits it. */
export function QuestionFlow(props: FlowProps) {
  const layout = flowLayout(props.data, props.info);
  if (layout === "list") return <ChecklistFlow {...props} />;
  return <CardsFlow {...props} live={layout === "live"} />;
}
