#!/usr/bin/env python3
"""Phase-1 coverage: does the concept lexicon recognise each dev query's subject?

A subject counts as correct when its top-5 UpToDate topics overlap those of
the query's pool hint (the drug monograph or the pooled concept). pool_* are
read here only as a diagnostic label; the lexicon never sees them.

    python3 docs/search/eval/lexicon_coverage.py --source /home/amir/Documents/UpToDate
"""

import argparse
from collections import Counter
import csv
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from apps.uptodate.search_concepts import ConceptLexicon, normalize  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--queries", type=Path, default=Path(__file__).with_name("dev-queries.csv"))
    parser.add_argument("--verbose", action="store_true", help="print every query")
    args = parser.parse_args()
    lexicon = ConceptLexicon.from_snapshot(args.source)
    search = sqlite3.connect((args.source / "search.db").resolve().as_uri() + "?mode=ro", uri=True)
    titles = {title.casefold(): str(key) for key, title in search.execute("SELECT id, title FROM topic")}

    def topics(key):
        return set(lexicon.concepts[key[2:]].topics["x"][:5]) if key.startswith("c:") else set()

    rows = list(csv.DictReader(args.queries.open(encoding="utf-8")))
    stats, misses = Counter(), []
    for row in rows:
        tagging = lexicon.tag(row["query"])
        subjects = tagging.keys("subject")
        intents = tagging.keys("intent") + tagging.keys("context") + tagging.keys("population")
        expected = set()
        if row["pool_drug"]:
            expected.add(titles.get(f"{row['pool_drug']}: drug information".casefold(), ""))
        for term in filter(None, (t.strip() for t in row["pool_concepts"].split(";"))):
            expected |= topics(lexicon.concept_key(term))
        expected.discard("")
        found = any(topics(key) & expected for key in subjects)
        translit = any(e.source == "translit" for s in tagging.spans for e in s.entries[:1])
        leftovers = [t for t in tagging.unknown if not t.isdigit()]
        stats["queries"] += 1
        stats["subject_correct"] += found
        stats["subject_any"] += bool(subjects)
        stats["via_translit"] += translit
        stats["intent_or_context"] += bool(intents)
        stats["no_unknown_words"] += not leftovers
        if row["category"] == "interaction":
            stats["interaction_two_drugs"] += len(subjects) >= 2
        if not found and row["expected_level"] != "lexicomp":
            misses.append((row["query_id"], row["query"], subjects, leftovers))
        if args.verbose:
            print(row["query_id"], row["query"], "| subj:", subjects, "| terms:", intents,
                  "| unknown:", leftovers, "| ok" if found else "| MISS")
    n = stats["queries"]
    for key, value in stats.items():
        print(f"{key}: {value}" + (f" ({value / n:.0%})" if key != "queries" else ""))
    print("subject misses (excluding interaction routing):")
    for miss in misses:
        print("  ", *miss)


if __name__ == "__main__":
    main()
