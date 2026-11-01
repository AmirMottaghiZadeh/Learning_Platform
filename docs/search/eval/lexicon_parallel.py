#!/usr/bin/env python3
"""Measure (and mine) the Persian lexicon on the project's own parallel text.

pipeline_v2.db holds an English and a Persian summary of each drug label
section, written bullet for bullet. Aligned bullet pairs give Persian medical
text whose English concepts are known. Drugs are split in two halves by a hash
of their name: half A may be mined for new Persian forms, half B is only
measured, so a gain on B is not tuned on B.

Recall counts an English clinical concept (not a drug, and named by the titles
of its own top UpToDate topics) as found when the Persian line yields a subject
whose top-5 topics overlap its own.

    backend/.venv/bin/python docs/search/eval/lexicon_parallel.py \\
        --source /home/amir/Documents/UpToDate \\
        --pipeline /home/amir/Documents/openfda/pipeline_v2.db eval
    ... mine --output /tmp/mined.tsv   # candidates from half A, for review
"""

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from apps.uptodate.search_concepts import ConceptLexicon, is_persian, normalize  # noqa: E402

SECTIONS = ("indications_and_usage", "adverse_reactions", "contraindications", "warnings", "boxed_warning",
            "pregnancy", "do_not_use")
QUERY_ROLES = {"stop", "intent", "context", "population", "route", "form"}
# English words the title test lets through although the label text does not use
# them as a concept: verbs ("may lead to", "trigger", "update"), adjectives
# ("high risk", "therapeutic levels") and bookkeeping nouns ("reproductive
# capacity", "alpha" in drug names). The English side misreads them, so a second
# number leaves them out; the full number is always printed first.
MISREAD_EN = frozenset("""high low lead trigger update therapeutic status capacity tests test alpha risk increased
decreased age years products outcomes history exposure laser gas tension""".split())


def bullet_pairs(pipeline):
    """{"A": [(english, persian)], "B": [...]}; sections whose bullet counts differ are skipped."""
    db = sqlite3.connect(Path(pipeline).resolve().as_uri() + "?mode=ro", uri=True)
    columns = ", ".join(f"{s}_summary_en, {s}_summary_fa" for s in SECTIONS)
    pairs = {"A": [], "B": []}
    try:
        for name, *values in db.execute(f"SELECT ingredient_name, {columns} FROM ingredient_clinical_profiles"):
            half = "AB"[int(hashlib.sha256(name.encode()).hexdigest(), 16) % 2]
            for english, persian in zip(values[::2], values[1::2]):
                en = [line.strip("-• ").strip() for line in (english or "").splitlines() if line.strip()]
                fa = [line.strip("-• ").strip() for line in (persian or "").splitlines() if line.strip()]
                if len(en) == len(fa):
                    pairs[half].extend(zip(en, fa))
    finally:
        db.close()
    return pairs


class Measure:
    def __init__(self, lexicon, source):
        self.lexicon = lexicon
        self.search = sqlite3.connect((Path(source) / "search.db").resolve().as_uri() + "?mode=ro", uri=True)
        self.titles = dict(self.search.execute("SELECT id, title FROM topic"))
        self._words = {}

    def topics(self, key):
        concept = self.lexicon.concepts.get(key[2:]) if key.startswith("c:") else None
        return set(concept.topics["x"][:5]) if concept else set()

    def title_words(self, key):
        if key not in self._words:
            words = set()
            for topic in self.lexicon.concepts[key[2:]].topics["x"][:3]:
                words |= {w[:5] for w in normalize(self.titles.get(int(topic), "")).split()}
            self._words[key] = words
        return self._words[key]

    def english_concepts(self, line):
        found = {}
        for span in self.lexicon.tag(line).spans:
            entry = span.entries[0]
            if (entry.role != "subject" or not entry.key.startswith("c:") or entry.kind == "drug"
                    or len(span.text) < 3 or self.lexicon.concepts[entry.key[2:]].weight < 100):
                continue
            # Drops everyday words that happen to be concepts ("risk", "who").
            if {w[:5] for w in span.text.split() if len(w) > 2} & self.title_words(entry.key):
                found[entry.key] = span.text
        return found

    def precision(self, pairs):
        """Share of concepts read from the Persian line that the English line also names
        (any concept, drugs included); low for words read as the wrong thing."""
        counts = Counter()
        for english, persian in pairs:
            tagging = self.lexicon.tag(persian)
            english_topics = [self.topics(key) for key in self.lexicon.tag(english).concepts()]
            for span in tagging.spans:
                entry = span.entries[0]
                if entry.role != "subject":
                    continue
                ok = any(self.topics(entry.key) & topics for topics in english_topics)
                group = "translit" if entry.source == "translit" else "lexicon"
                counts[group] += 1
                counts[group + "_ok"] += ok
        return counts

    def unconfirmed(self, pairs, seed=7, lexicon_n=150, translit_n=100):
        """Random readings of the Persian side that the English line does not name, for hand review."""
        import random
        found = {"lexicon": [], "translit": []}
        for english, persian in pairs:
            tagging = self.lexicon.tag(persian)
            english_topics = [self.topics(key) for key in self.lexicon.tag(english).concepts()]
            for span in tagging.spans:
                entry = span.entries[0]
                if entry.role != "subject" or any(self.topics(entry.key) & t for t in english_topics):
                    continue
                group = "translit" if entry.source == "translit" else "lexicon"
                label = self.lexicon.concepts[entry.key[2:]].label if entry.key[2:] in self.lexicon.concepts else entry.key
                found[group].append((group, span.text, label, entry.kind, entry.source, english, persian))
        rng = random.Random(seed)
        return (rng.sample(found["lexicon"], min(lexicon_n, len(found["lexicon"])))
                + rng.sample(found["translit"], min(translit_n, len(found["translit"])))), {g: len(v) for g, v in found.items()}

    def recall(self, pairs):
        total = hit = 0
        seen, missed, labels = Counter(), Counter(), {}
        for english, persian in pairs:
            targets = self.english_concepts(english)
            if not targets:
                continue
            found = [self.topics(key) for key in self.lexicon.tag(persian).concepts()]
            for key, text in targets.items():
                ok = any(self.topics(key) & topics for topics in found)
                total, hit = total + 1, hit + ok
                seen[key] += 1
                missed[key] += not ok
                labels[key] = text
        return total, hit, seen, missed, labels

    def misses(self, pairs):
        """Why each English concept was missed: no Persian form at all, or a form the text did not use."""
        keys, firsts = set(), set()
        for form, entries in self.lexicon.forms.items():
            if is_persian(form) and entries[0].role == "subject":
                keys.add(entries[0].key)
                firsts.update(list(self.topics_ranked(entries[0].key))[:1])
        stats = {}
        for english, persian in pairs:
            targets = self.english_concepts(english)
            if not targets:
                continue
            found = [self.topics(key) for key in self.lexicon.tag(persian).concepts()]
            for key, text in targets.items():
                row = stats.setdefault(key, {"label": text, "seen": 0, "missed": 0, "examples": []})
                row["seen"] += 1
                if not any(self.topics(key) & topics for topics in found):
                    row["missed"] += 1
                    if len(row["examples"]) < 2:
                        row["examples"].append(persian)
        for key, row in stats.items():
            first = self.topics_ranked(key)[:1]
            row["kind"] = "variant" if key in keys or (first and first[0] in firsts) else "absent"
        return stats

    def topics_ranked(self, key):
        concept = self.lexicon.concepts.get(key[2:]) if key.startswith("c:") else None
        return concept.topics["x"] if concept else []

    def mine(self, pairs, missed):
        """Dice association between still-missed English concepts and Persian n-grams."""
        count_t, count_g, count_tg = Counter(), Counter(), Counter()
        for english, persian in pairs:
            targets = [key for key in self.english_concepts(english) if missed[key]]
            tokens = [self.lexicon.stem(t) for t in normalize(persian).split()]
            roles = [(self.lexicon.forms.get(t) or [None])[0] for t in tokens]
            grams = set()
            for i in range(len(tokens)):
                for j in range(i + 1, min(i + 4, len(tokens)) + 1):
                    edge = [roles[i], roles[j - 1]]
                    if all(map(is_persian, tokens[i:j])) and not any(e and e.role in QUERY_ROLES for e in edge):
                        grams.add(" ".join(tokens[i:j]))
            count_g.update(grams)
            for key in targets:
                count_t[key] += 1
                count_tg.update((key, gram) for gram in grams)
        ranked = {}
        for (key, gram), n in count_tg.items():
            dice = 2 * n / (count_t[key] + count_g[gram])
            if n >= 3 and dice >= 0.3:
                # Prefer the fuller phrase on near ties.
                ranked.setdefault(key, []).append((dice + 0.02 * len(gram.split()), gram, n, dice))
        rows = []
        for key, candidates in ranked.items():
            for _, gram, n, dice in sorted(candidates, reverse=True):
                # A phrase the lexicon already reads as this concept teaches nothing.
                if not any(self.topics(key) & self.topics(span.entries[0].key)
                           for span in self.lexicon.tag(gram).spans if span.entries[0].role == "subject"):
                    rows.append((key, gram, n, dice, count_t[key]))
                    break
        return sorted(rows, key=lambda r: -r[4])


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--pipeline", type=Path, required=True)
    parser.add_argument("--lexicon", type=Path, help="lexicon directory (default: the versioned one)")
    parser.add_argument("action", choices=("eval", "mine", "misses", "precision-sample"))
    parser.add_argument("--output", type=Path, help="mine/misses: TSV written for review")
    args = parser.parse_args()
    lexicon = ConceptLexicon.from_snapshot(args.source, *([args.lexicon] if args.lexicon else []))
    measure = Measure(lexicon, args.source)
    pairs = bullet_pairs(args.pipeline)
    if args.action == "precision-sample":
        rows, totals = measure.unconfirmed(pairs["A"])
        print(f"half A unconfirmed readings: {totals}")
        with args.output.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write("\t".join(row) + "\n")
        print(f"{len(rows)} sampled -> {args.output}")
        return
    if args.action == "misses":
        stats = measure.misses(pairs["A"])
        totals = Counter()
        for row in stats.values():
            totals[row["kind"]] += row["missed"]
            totals["seen"] += row["seen"]
        print(f"half A misses by kind: {dict(totals)}")
        with args.output.open("w", encoding="utf-8") as handle:
            for key, row in sorted(stats.items(), key=lambda kv: -kv[1]["missed"]):
                if row["missed"]:
                    handle.write("\t".join([row["label"], row["kind"], str(row["missed"]), str(row["seen"]),
                                            *row["examples"]]) + "\n")
        return
    half = "B" if args.action == "eval" else "A"
    total, hit, seen, missed, labels = measure.recall(pairs[half])
    covered = sum(1 for key in seen if missed[key] < seen[key])
    print(f"half {half}: {len(pairs[half])} bullet pairs; English clinical concepts {total}, "
          f"found in Persian {hit} ({hit / total:.1%}); distinct concepts found at least once "
          f"{covered}/{len(seen)} ({covered / len(seen):.1%})")
    generic = [key for key in seen if labels[key] in MISREAD_EN]
    clean_total = total - sum(seen[key] for key in generic)
    clean_hit = hit - sum(seen[key] - missed[key] for key in generic)
    print(f"without {len(generic)} misread English words: {clean_hit}/{clean_total} ({clean_hit / clean_total:.1%})")
    if args.action == "eval":
        counts = measure.precision(pairs[half])
        for group in ("lexicon", "translit"):
            n, ok = counts[group], counts[group + "_ok"]
            print(f"Persian concepts from {group}: {n}, also named in the English line {ok} ({ok / max(n, 1):.1%})")
    if args.action == "mine":
        rows = measure.mine(pairs["A"], missed)
        with args.output.open("w", encoding="utf-8") as handle:
            for key, gram, n, dice, count in rows:
                handle.write(f"{labels[key]}\t{gram}\t{n}\t{count}\t{dice:.2f}\n")
        print(f"{len(rows)} candidates -> {args.output}")


if __name__ == "__main__":
    main()
