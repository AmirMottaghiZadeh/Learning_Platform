#!/usr/bin/env python3
"""Transliteration alone on the project's Persian drug names.

Every `project` row of drugs_fa.csv is hidden from the lexicon, so only
transliteration can read it; the drug still counts as on the Iranian market.
Precision is over names transliteration answered, recall over all names. Run
once without and once with drug context («دوز ...»).

    backend/.venv/bin/python docs/search/eval/translit_recall.py --source /home/amir/Documents/UpToDate
"""

import argparse
import csv
from pathlib import Path
import shutil
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from apps.uptodate.search_concepts import LEXICON_DIR, ConceptLexicon, normalize  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    names = [r for r in csv.DictReader((LEXICON_DIR / "drugs_fa.csv").open(encoding="utf-8"))
             if r["status"] == "project"]
    lexicon_dir = Path(tempfile.mkdtemp())
    try:
        for path in LEXICON_DIR.iterdir():
            if path.name != "drugs_fa.csv":
                shutil.copy(path, lexicon_dir / path.name)
        (lexicon_dir / "drugs_fa.csv").write_text("fa,en,key,article_id,method,status\n", encoding="utf-8")
        lexicon = ConceptLexicon.from_snapshot(args.source, lexicon_dir)
    finally:
        shutil.rmtree(lexicon_dir)
    lexicon.market |= {r["key"] for r in names}
    for context in (False, True):
        start, answered, correct = time.time(), 0, 0
        for row in names:
            hit = lexicon.transliterate(normalize(row["fa"]), context=context)
            answered += bool(hit)
            correct += bool(hit and hit[2].key == row["key"])
        print(f"context={context}: {len(names)} names, answered {answered}, correct {correct}, "
              f"precision {correct / max(answered, 1):.1%}, recall {correct / len(names):.1%} "
              f"[{(time.time() - start) / len(names) * 1000:.1f} ms/name]")


if __name__ == "__main__":
    main()
