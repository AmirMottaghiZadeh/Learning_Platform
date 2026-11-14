/** In-memory render timing only: never questions, source text, account IDs or tokens. */
type Sample = { started: number; titles: boolean; citation: boolean; finished: boolean };
const samples = new Map<string, Sample>();
const now = () => typeof performance !== "undefined" ? performance.now() : Date.now();

export function startReferenceTiming(id: string) {
  if (samples.size >= 100) samples.delete(samples.keys().next().value!);
  samples.set(id, { started: now(), titles: false, citation: false, finished: false });
}

export function cancelReferenceTiming(id: string) { samples.delete(id); }

export function noteReferenceRender(id: string, state: { status: string; titles: boolean; citation: boolean; answerComplete: boolean }) {
  const sample = samples.get(id);
  if (!sample || sample.finished) return; // Restoring an old job is not a new measurement.
  const ended = now();
  const record = (name: string, complete = false) => {
    try {
      if (typeof performance !== "undefined" && typeof performance.measure === "function") {
        performance.measure(`pharmenta.reference.${name}`, { start: sample.started, end: ended,
          detail: { turn_id: id, status: state.status, answer_complete: complete, elapsed_ms: ended - sample.started } });
      }
    } catch { /* Unsupported native performance APIs must never affect search. */ }
  };
  if (state.titles && !sample.titles) { sample.titles = true; record("titles"); }
  if (state.citation && !sample.citation) { sample.citation = true; record("first_citation"); }
  if (state.status !== "running") {
    sample.finished = true;
    record("finished", state.status === "complete" && state.answerComplete);
  }
}
