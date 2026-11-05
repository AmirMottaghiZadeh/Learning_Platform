"""Snapshot search aliases and curated topic associations, shared with offline.

This deliberately has no Django or embedding dependency. Only known snapshot
associations expand a query; ordinary title search remains the fallback.
"""

import bisect
from dataclasses import dataclass
import re

from .text import plain_title


def normalize(value):
    return " ".join(re.findall(r"[a-z0-9؀-ۿ]+", plain_title(value).lower()))


def suggestion_kind(query):
    for kind, pattern in (
        ("treatment", r"treat|therap|management|regimen"),
        ("followup", r"follow|cure|monitor"),
        ("diagnosis", r"diagnos|test|screen|symptom"),
    ):
        if re.search(pattern, normalize(query)):
            return kind
    return "general"


@dataclass
class SearchCatalog:
    queries: list
    topics: dict

    def __post_init__(self):
        self.aliases = {}
        for word, concept, weight in self.queries:
            key = normalize(word)
            previous = self.aliases.get(key)
            if key and (previous is None or weight > previous[1]):
                self.aliases[key] = (str(concept), weight)
        explicit = set(self.aliases)
        for word, concept, weight in self.queries:
            key = normalize(re.sub(r"\([^)]*\)", "", word))
            previous = self.aliases.get(key)
            if key and key not in explicit and (previous is None or weight > previous[1]):
                self.aliases[key] = (str(concept), weight)
        self.vocab = sorted(self.aliases)

    @classmethod
    def from_rows(cls, queries, topics):
        queries = [[plain_title(word), str(cid), int(weight or 0)] for cid, word, weight in queries if word]
        used = {row[1] for row in queries}
        # Keep the source's compact CSVs, not millions of individually allocated
        # ID strings in every phone's memory. Split only the requested list.
        return cls(queries, {str(cid): [hits or "" for hits in lists]
                             for cid, *lists in topics if str(cid) in used})

    def export(self):
        return {"queries": self.queries, "topics": self.topics}

    def resolve(self, query):
        """Exact alias first; otherwise the longest complete alias in the query.

        Remaining words still constrain titles, so 'h pylori refractory' does
        not silently become an unrestricted search for H. pylori.
        """
        words = normalize(query).split()[:8]
        for length in range(len(words), 0, -1):
            for start in range(len(words) - length + 1):
                alias = " ".join(words[start:start + length])
                match = self.aliases.get(alias)
                if match:
                    return match[0], words[:start] + words[start + length:], alias
        return None, words, ""

    def hits(self, concept, query):
        lists = self.topics.get(concept, [])
        words = set(normalize(query).split())
        audience = 3 if {"patient", "education"} <= words else 2 if words & {
            "child", "children", "pediatric", "paediatric", "infant", "infants"
        } else 1 if words & {"adult", "adults"} else 0
        preferred = lists[audience] if len(lists) > audience else ""
        hits = preferred or (lists[0] if lists else "")
        return list(dict.fromkeys(t.strip() for t in hits.split(",") if t.strip()))

    def suggest(self, query, valid_ids, limit=12):
        prefix = normalize(query)
        if len(prefix) < 2:
            return []
        current = self.aliases.get(prefix, (None, 0))[0]
        candidates = {}
        at = bisect.bisect_left(self.vocab, prefix)
        while at < len(self.vocab) and self.vocab[at].startswith(prefix):
            word = self.vocab[at]
            cid, weight = self.aliases[word]
            if cid != current and any(t in valid_ids for t in self.hits(cid, word)):
                key = (-weight, len(word), word)
                if cid not in candidates or key < candidates[cid][0]:
                    candidates[cid] = (key, word)
            at += 1
        return [{
            "query": word, "label": word, "kind": suggestion_kind(word),
            "count": sum(t in valid_ids for t in self.hits(self.aliases[word][0], word)),
        } for _, word in sorted(candidates.values())[:limit]]
