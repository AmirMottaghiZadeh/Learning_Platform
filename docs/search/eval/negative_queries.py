#!/usr/bin/env python3
"""Precision on users' language: does the lexicon read a wrong subject?

negative-queries.csv holds four groups: natural sentences around a known
subject, questions with no medical subject, ordinary words that look like drug
names, and misspelt drug names. `required` subjects must be found; `allowed`
ones may appear. Any other subject is a false subject. A body part (kind
anatomy) is a modifier, never counted as false.

    backend/.venv/bin/python docs/search/eval/negative_queries.py --source /home/amir/Documents/UpToDate
"""

import argparse
from collections import Counter
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from apps.uptodate.search_concepts import ConceptLexicon  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--queries", type=Path, default=Path(__file__).with_name("negative-queries.csv"))
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    lexicon = ConceptLexicon.from_snapshot(args.source)

    def topics(key):
        concept = lexicon.concepts.get(key[2:]) if key.startswith("c:") else None
        return set(concept.topics["x"][:5]) if concept else set()

    def keys(names):
        return [lexicon.concept_key(n.strip()) for n in names.split(";") if n.strip()]

    stats, failures = Counter(), []
    for row in csv.DictReader(args.queries.open(encoding="utf-8")):
        tagging = lexicon.tag(row["query"])
        required, allowed = keys(row["required"]), keys(row["allowed"])
        expected = [topics(k) | {k} for k in required + allowed]
        subjects = [(span.text, span.entries[0]) for span in tagging.spans if span.entries[0].role == "subject"]
        false = [text for text, entry in subjects if entry.kind != "anatomy"
                 and not any((topics(entry.key) | {entry.key}) & e for e in expected)]
        found = [k for k in required if any(topics(entry.key) & (topics(k) | {k}) or entry.key == k
                                            for _, entry in subjects)]
        missed = [k for k in required if k not in found]
        category = row["category"]
        stats[category, "queries"] += 1
        stats[category, "false"] += bool(false)
        stats[category, "missed"] += bool(missed)
        if false or missed:
            failures.append((row["query_id"], category, row["query"], false,
                             [lexicon.concepts[k[2:]].label for k in missed]))
        if args.verbose:
            print(row["query_id"], row["query"], [(t, e.key, e.source) for t, e in subjects])
    total = sum(v for (c, k), v in stats.items() if k == "queries")
    false_total = sum(v for (c, k), v in stats.items() if k == "false")
    for category in dict.fromkeys(c for c, _ in stats):
        n = stats[category, "queries"]
        print(f"{category:11} queries {n:3}  false subject {stats[category, 'false']:3} "
              f"({stats[category, 'false'] / n:.1%})  required missed {stats[category, 'missed']:3}")
    print(f"total: {total} queries, false-subject rate {false_total / total:.1%}")
    for failure in failures:
        print("  ", *failure)


if __name__ == "__main__":
    main()
