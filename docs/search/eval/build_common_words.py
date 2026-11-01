#!/usr/bin/env python3
"""Build search_lexicon/common_fa.txt: Persian words transliteration must not read as names.

A word goes on the list when the project's own parallel text shows it is
ordinary Persian: transliteration turns it into a drug or disease that the
aligned English line does not name. Only half A of pipeline_v2.db is used
(see lexicon_parallel.py), plus the study-content flashcards and questions of
half-A drugs, so half B stays a clean test.

With --frequency, the most frequent words of a general Persian corpus join the
list when transliteration reads them as a name. Lexicon forms and project drug
names never do. Among the COMMON_RANK most frequent words every such reading
was wrong on review («هزار» Hyzaar, «کتاب» K-Tab), so all of them join. Below
that rank a word joins on a match under CLOSE_MATCH or a brand name; a generic
drug or disease name at CLOSE_MATCH or above is kept: «رادیولوژی»,
«گلوبولین» are real names that Wikipedia also uses. The corpus used is the
Leipzig Corpora Collection pes_wikipedia_2021_1M (its -words.txt file:
id, word, frequency); only the word list is used, never its sentences.

    backend/.venv/bin/python docs/search/eval/build_common_words.py \\
        --source /home/amir/Documents/UpToDate \\
        --pipeline /home/amir/Documents/openfda/pipeline_v2.db \\
        --study /home/amir/Documents/openfda/study_content/study_content.db \\
        --frequency /home/amir/Documents/pharmenta-search-eval/downloads/leipzig-pes-wikipedia-2021-1M/pes_wikipedia_2021_1M/pes_wikipedia_2021_1M-words.txt
"""

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).parent))
from apps.uptodate.search_concepts import LEXICON_DIR, ConceptLexicon, is_persian, normalize  # noqa: E402
from lexicon_parallel import Measure, bullet_pairs  # noqa: E402

HEADER = """# Ordinary Persian words that drug- and disease-name transliteration misread
# (نادر is not Toradol). Built by docs/search/eval/build_common_words.py from
# half A of the parallel text{frequency}; do not edit by hand, rebuild instead.
"""
CLOSE_MATCH = 0.9
COMMON_RANK = 10000
FREQUENCY_SOURCE = " and the word frequencies of\n# Leipzig Corpora Collection pes_wikipedia_2021_1M"


def study_pairs(study, pipeline):
    """(english, persian) flashcard items, question stems and options of half-A drugs."""
    db = sqlite3.connect(Path(pipeline).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        half_a = {rxcui for rxcui, name in db.execute(
            "SELECT ingredient_rxcui, ingredient_name FROM ingredient_clinical_profiles")
            if int(hashlib.sha256(name.encode()).hexdigest(), 16) % 2 == 0}
    finally:
        db.close()
    db = sqlite3.connect(Path(study).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        rows = list(db.execute("SELECT f.rxcui, i.text_en, i.text_fa FROM flashcard_item i "
                               "JOIN flashcard f ON f.id = i.flashcard_id"))
        rows += list(db.execute("SELECT rxcui, stem_en, stem_fa FROM question"))
        rows += list(db.execute("SELECT q.rxcui, o.text_en, o.text_fa FROM question_option o "
                                "JOIN question q ON q.id = o.question_id"))
    finally:
        db.close()
    return [(en, fa) for rxcui, en, fa in rows if str(rxcui) in half_a and en and fa]


def frequent_words(path, top):
    """The `top` most frequent single Persian words of a Leipzig -words.txt file, normalized."""
    rows = []
    for line in Path(path).open(encoding="utf-8"):
        parts = line.rstrip("\n").split("\t")
        if len(parts) == 3 and parts[2].isdigit():
            rows.append((int(parts[2]), parts[1]))
    words = {}
    for _, word in sorted(rows, reverse=True):
        word = normalize(word)
        if word and " " not in word and is_persian(word):
            words.setdefault(word)
            if len(words) == top:
                break
    return list(words)


def misread_frequent(lexicon, words):
    """Frequent words transliteration misreads as a drug or disease name."""
    found = {}
    for rank, word in enumerate(words, 1):
        token = lexicon.stem(word)
        if token in lexicon.forms:
            continue
        known = token in lexicon.vocab
        hits = [h for h in (lexicon.transliterate(token, context=True, known=known),
                            lexicon.transliterate(token, conditions=True, known=known)) if h]
        if not hits:
            continue
        best = max(hits, key=lambda h: h[0])
        if rank <= COMMON_RANK or best[0] < CLOSE_MATCH or "brand" in best[3]:
            found[word] = best
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--pipeline", type=Path, required=True)
    parser.add_argument("--study", type=Path)
    parser.add_argument("--frequency", type=Path, help="Leipzig -words.txt of a general Persian corpus")
    parser.add_argument("--top", type=int, default=50000, help="--frequency: how many frequent words to check")
    parser.add_argument("--review", type=Path, help="--frequency: TSV of added words and their misreading")
    parser.add_argument("--output", type=Path, default=LEXICON_DIR / "common_fa.txt")
    args = parser.parse_args()

    # Measure transliteration as it is without the current list.
    lexicon_dir = Path(tempfile.mkdtemp())
    try:
        for path in LEXICON_DIR.iterdir():
            if path.name != "common_fa.txt":
                shutil.copy(path, lexicon_dir / path.name)
        lexicon = ConceptLexicon.from_snapshot(args.source, lexicon_dir)
    finally:
        shutil.rmtree(lexicon_dir)
    measure = Measure(lexicon, args.source)
    pairs = bullet_pairs(args.pipeline)["A"]
    if args.study:
        pairs += study_pairs(args.study, args.pipeline)

    seen, confirmed, best = Counter(), Counter(), {}
    for english, persian in pairs:
        spans = [s for s in lexicon.tag(persian).spans if s.entries[0].source == "translit" and " " not in s.text]
        if not spans:
            continue
        english_topics = [measure.topics(key) for key in lexicon.tag(english).concepts()]
        for span in spans:
            seen[span.text] += 1
            confirmed[span.text] += any(measure.topics(span.entries[0].key) & t for t in english_topics)
            best[span.text] = max(best.get(span.text, 0), span.score)
    words = sorted(w for w in seen
                   if (seen[w] >= 2 and confirmed[w] / seen[w] < 0.2)
                   or (seen[w] == 1 and not confirmed[w] and best[w] < 0.9))
    total, ok = sum(seen.values()), sum(confirmed.values())
    print(f"{len(pairs)} pairs; transliterated words {len(seen)} ({total} times, {ok} confirmed by English); "
          f"{len(words)} from the parallel text")
    if args.frequency:
        frequent = misread_frequent(lexicon, frequent_words(args.frequency, args.top))
        print(f"{len(frequent)} of the {args.top} most frequent corpus words are misread by transliteration")
        if args.review:
            with args.review.open("w", encoding="utf-8") as handle:
                for word, (score, form, entry, why, _) in frequent.items():
                    handle.write(f"{word}\t{score:.3f}\t{form}\t{entry.kind}\t{why}\n")
        words = sorted(set(words) | set(frequent))
    header = HEADER.format(frequency=FREQUENCY_SOURCE if args.frequency else "")
    args.output.write_text(header + "\n".join(words) + "\n", encoding="utf-8")
    print(f"{len(words)} written to {args.output}")


if __name__ == "__main__":
    main()
