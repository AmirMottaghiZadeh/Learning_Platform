"""Persian/English concept lexicon for the offline UpToDate search; no model.

English concepts, their surface forms (synonyms, brands, common misspellings)
and ranked topics come from UpToDate's search.db. Persian forms come from the
versioned CSV files in search_lexicon/. A query is tagged by longest match
over both; unknown Persian words fall back to a transliteration skeleton
matched against drug names. See docs/14-search-architecture-proposal.fa.md.
"""

from collections import defaultdict
import csv
from dataclasses import dataclass, field, replace
from pathlib import Path
import re
import sqlite3
import unicodedata

LEXICON_DIR = Path(__file__).with_name("search_lexicon")
LEXICON_VERSION = "utd-lexicon-v1"
AUDIENCES = ("x", "a", "p", "i")
ROLES = frozenset({"subject", "intent", "context", "population", "route", "form", "stop"})
KINDS = frozenset({"condition", "symptom", "test", "class", "organism", "drug", "anatomy"})
MAX_SPAN = 8
# Disease-name transliteration is a fallback: only for a query with no other
# subject, only for long unknown words, and stricter than for drug names.
CONDITION_TRANSLIT = 0.85
CONDITION_MIN_LETTERS = 6
CONDITION_MIN_WEIGHT = 300
# Short Persian words are mostly ordinary words (نظر, ذکر, نیست); a drug name
# that short must match almost exactly.
SHORT_WORD_LETTERS = 4
SHORT_WORD_TRANSLIT = 0.9
VOCAB_TRANSLIT = 0.9
# Drug-name transliteration threshold, raised for what is least likely meant:
# a foreign brand name, a drug the project does not list (not on the Iranian
# market), a Persian word without a generic-name stem (-پریل, -سارتان);
# lowered when the query talks about a drug (dose, side effects, tablet).
BRAND_PENALTY = 0.07
OFF_MARKET_PENALTY = 0.05
NO_STEM_PENALTY = 0.03
CONTEXT_BONUS = 0.03
MAX_TRANSLIT = 0.95
# Below this a transliteration is shown to the user as «منظورتان … بود؟».
CONFIRM_SCORE = 0.95
DRUG_CONTEXT = frozenset({
    "intent:dosing", "intent:adverse", "intent:interaction", "intent:food_interaction", "intent:mechanism",
    "intent:pharmacokinetics", "intent:administration", "intent:dosage_forms", "intent:indications",
    "intent:contraindications", "intent:warnings", "intent:monitoring", "intent:storage", "intent:brand",
    "intent:overdose", "intent:alternative", "intent:discontinuation", "intent:missed_dose", "intent:price"})
# Punctuation ends a phrase: «استفراغ، تشنج، تب» is not «تشنج تب».
_SEGMENT = re.compile(r"[,،;؛:!?؟()\[\]{}/\\|«»\"\n]+|(?<!\d)\.|\.(?!\d)")

_FA_CHARS = str.maketrans({
    "ي": "ی", "ى": "ی", "ئ": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه", "أ": "ا", "إ": "ا", "ٱ": "ا",
    "ؤ": "و", "ء": "", "ـ": "", "‌": " ", "‍": "", "‏": "", "‎": "",
    "٫": ".", "٬": ",", "،": " ", "؛": " ", "؟": " ",
})
_MARKS = re.compile(r"[ً-ٰٟۖ-ۭ]")
_TOKEN = re.compile(r"[^\W_]+(?:\.\d+)?|[<>]=?", re.UNICODE)
_PERSIAN = re.compile(r"[؀-ۿ]")
_PAREN = re.compile(r"\s*\([^)]*\)")
# Affixes written apart: plurals ("عفونت‌های ادراری"), the ezafe «ی» ("قفسه‌ی
# سینه"), comparatives ("شایع‌ترین"), the verb prefix ("می‌شود") and
# possessives ("بچه‌ام", "معده‌اش").
_DETACHED = frozenset({"ها", "های", "هایی", "ی", "تر", "ترین", "می", "نمی", "ات", "اش", "شان", "مان", "تان"})
# «ام» stays: it is also the letter M of abbreviations (ام اس, ای ام دی); alone it is a stop word.
# Words that may sit inside a phrase without breaking it ("افت شدید فشار خون").
_MODIFIER_KEYS = frozenset({"context:acute", "context:chronic", "context:severe", "context:mild", "stop:modifier"})
MAX_GAPS = 2
# Organ nouns and their adjectives, swapped inside Persian phrases ("بیماری قلب" ↔ "بیماری قلبی").
_ADJECTIVES = {"قلب": "قلبی", "کبد": "کبدی", "کلیه": "کلیوی", "ریه": "ریوی", "مغز": "مغزی", "پوست": "پوستی",
               "عصب": "عصبی", "استخوان": "استخوانی", "عضله": "عضلانی", "چشم": "چشمی", "مفصل": "مفصلی",
               "تیروئید": "تیروئیدی", "عروق": "عروقی", "گوارش": "گوارشی", "ادرار": "ادراری", "تنفس": "تنفسی",
               "خون": "خونی", "رحم": "رحمی", "پستان": "پستانی", "صفرا": "صفراوی", "دهان": "دهانی", "معده": "معدی"}
_SWAPS = {**_ADJECTIVES, **{v: k for k, v in _ADJECTIVES.items()}, "کم": "پایین", "پایین": "کم", "زیاد": "بالا",
          "بالا": "زیاد"}
# Joined suffixes stripped from an unknown word when the stem is known.
_SUFFIXES = ("هایشان", "هایمان", "هایش", "هایم", "هایت", "هایی", "های", "ها", "شان", "مان", "تان", "یش", "یم",
             "ام", "ش", "م", "ت", "ی")  # plural, possessive (فشارش, چشمام), adjective (دیابتی)
# Letters Persian writers confuse because they sound alike (اسحال → اسهال).
# ع/ا is left out: it turns ordinary words into others (بعید → باید). A
# one-letter-off correction was tried and dropped: medical words that differ
# by one letter mean different things (هیپوپلازی/هیپرپلازی, نوروتوکسیک/نفروتوکسیک).
_HOMOPHONES = str.maketrans({"ط": "ت", "ص": "س", "ث": "س", "ذ": "ز", "ض": "ز", "ظ": "ز", "ح": "ه", "غ": "ق"})


def normalize(text: str) -> str:
    """Canonical token string for lexicon keys and queries; never for display."""
    text = unicodedata.normalize("NFKC", text or "").translate(_FA_CHARS)
    text = "".join(str(unicodedata.digit(c)) if c.isdecimal() else c for c in _MARKS.sub("", text))
    return " ".join(t for t in _TOKEN.findall(text.casefold()) if t not in _DETACHED)


def is_persian(text: str) -> bool:
    return bool(_PERSIAN.search(text))


# Transliteration: both scripts map to one rough Latin spelling. Letters that
# Persian spelling of Latin drug names merges (s/z, t, k/q, e/i, o/u/v) are
# folded together. The skeleton keeps consonants; the full form adds the
# vowels Persian writes (ا و ی), which breaks ties such as atenolol/ethanol.
_FA_LETTERS = {
    "ب": "b", "پ": "p", "ت": "t", "ط": "t", "ث": "s", "س": "s", "ص": "s", "ز": "s", "ذ": "s",
    "ض": "s", "ظ": "s", "ج": "j", "چ": "c", "ح": "h", "ه": "h", "خ": "x", "د": "d", "ر": "r",
    "ژ": "j", "ش": "S", "غ": "g", "ف": "f", "ق": "k", "ک": "k", "گ": "g", "ل": "l", "م": "m",
    "ن": "n", "و": "u", "ی": "i", "ا": "a", "آ": "a",
}
# Persian names of diseases follow French endings (hépatite → هپاتیت).
_FRENCH_ENDINGS = ((r"itis$", "it"), (r"osis$", "os"), (r"emia$", "mi"), (r"ia$", "i"), (r"y$", "i"),
                   (r"ae$", ""), (r"us$", ""), (r"um$", ""))
_EN_RULES = ((r"ph", "f"), (r"th", "t"), (r"ch", "k"), (r"sh", "S"), (r"ck", "k"), (r"qu", "k"),
             (r"^x", "s"), (r"x", "ks"), (r"c(?=[eiy])", "s"), (r"c", "k"), (r"g(?=[eiy])", "j"),
             (r"q", "k"), (r"z", "s"), (r"[wvou]", "u"), (r"[eiy]", "i"))


def _collapse(text):
    return re.sub(r"(.)\1+", r"\1", text)


def letters_fa(text: str) -> str:
    words = ["".join(_FA_LETTERS.get(c, "") for c in word) for word in normalize(text).split()]
    # A word-final ه is usually a written vowel (-e), not h: «مونته لوکاست».
    out = "".join(w[:-1] if len(w) > 3 and w.endswith("h") else w for w in words)
    return _collapse(out.replace("gs", "ks"))  # «گز» spells x: دگزامتازون = dexamethasone


def letters_en(text: str, *, french: bool = False) -> str:
    out = re.sub(r"[^a-z]", "", normalize(text))
    for pattern, repl in _FRENCH_ENDINGS if french else ():
        out = re.sub(pattern, repl, out)
    for pattern, repl in _EN_RULES:
        out = re.sub(pattern, repl, out)
    return _collapse(out)


def consonants(letters: str) -> str:
    return _collapse(re.sub(r"[aiu]", "", letters))


def skeleton_fa(text: str) -> str:
    return consonants(letters_fa(text))


def skeleton_en(text: str) -> str:
    return consonants(letters_en(text))


def similarity(a: str, b: str, floor: float = 0.0) -> float:
    """1 - Levenshtein distance / longer length; 0.0 as soon as it must fall below floor."""
    if not a or not b:
        return 0.0
    longest = max(len(a), len(b))
    limit = int((1 - floor) * longest + 1e-9)
    if abs(len(a) - len(b)) > limit:
        return 0.0
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        if min(current) > limit:
            return 0.0
        previous = current
    return 1 - previous[-1] / longest if previous[-1] <= limit else 0.0


@dataclass(frozen=True)
class Entry:
    key: str          # "c:<concept id>" for UpToDate concepts, else "<role>:<name>"
    role: str
    kind: str = ""    # drug | term | one of KINDS
    source: str = ""  # search.db | drugs_fa | concepts_fa | terms | translit
    status: str = ""


@dataclass
class Concept:
    concept_id: str
    kind: str
    weight: int
    label: str
    topics: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    text: str
    entries: tuple
    score: float = 1.0
    gaps: tuple = ()  # token positions skipped inside the span (modifiers)
    reason: str = ""  # why a transliteration passed (brand, off-market, stem, context)
    alternatives: tuple = ()  # (concept key, score) of the next candidates


@dataclass(frozen=True)
class Tagging:
    tokens: tuple
    spans: tuple
    unknown: tuple

    embedded: tuple = ()
    respelled: tuple = ()  # (written, read as) for same-sounding misspellings

    def keys(self, role):
        spans = sorted(self.spans + self.embedded, key=lambda span: span.start)
        return list(dict.fromkeys(entry.key for span in spans for entry in span.entries[:1]
                                  if entry.role == role))

    def concepts(self):
        """Every concept the query names: subjects, the concept behind a context
        phrase («نارسایی کبد» is the liver context and also hepatic failure), and
        the second concept of a shared Persian word."""
        found = []
        for span in sorted(self.spans, key=lambda span: span.start):
            first, *rest = span.entries
            second = rest[:1] if first.role != "subject" else []
            found.extend(entry.key for entry in [first, *second] if entry.role == "subject")
            found.extend(entry.key for entry in rest if entry.status == "shared")
        return list(dict.fromkeys(found))

    def interpretation(self):
        """How each subject was read, for «منظورتان … بود؟». `confirm` marks a reading
        the engine is not sure of: a transliteration below CONFIRM_SCORE or of a
        disease name, a word shared by two concepts, a context decision, a respelling."""
        items = []
        for span in sorted(self.spans, key=lambda span: span.start):
            entry = span.entries[0]
            if entry.role != "subject":
                continue
            shared = [(e.key, None) for e in span.entries[1:] if e.status == "shared"]
            items.append({
                "text": span.text, "key": entry.key, "kind": entry.kind, "source": entry.source,
                "score": round(span.score, 3), "reason": span.reason,
                "alternatives": [{"key": k, "score": None if v is None else round(v, 3)}
                                 for k, v in list(span.alternatives) + shared],
                "confirm": (entry.source == "translit" and (entry.kind == "condition" or span.score < CONFIRM_SCORE))
                           or bool(shared) or entry.source == "disambiguation",
            })
        items.extend({"text": written, "respelled": read, "confirm": True} for written, read in self.respelled)
        return items


def phrase_variants(form):
    """Other ways of writing a Persian phrase: organ noun ↔ adjective, کم ↔ پایین,
    «X پایین/بالا» → «کاهش/افت/افزایش X», without «دستگاه», and with the ezafe «ی» after a vowel. The opposite direction is not
    generated: «کاهش وزن» is weight loss, «وزن پایین» is underweight."""
    tokens = form.split()
    if len(tokens) < 2 or not is_persian(form):
        return set()
    found = {" ".join(tokens[:i] + [_SWAPS[t]] + tokens[i + 1:]) for i, t in enumerate(tokens) if t in _SWAPS}
    if "دستگاه" in tokens[1:] and len(tokens) > 2:  # "عفونت دستگاه تنفسی" = "عفونت تنفسی"
        found.add(" ".join(t for t in tokens if t != "دستگاه"))
    # The ezafe after a vowel is written: «ریزش موی سر», «زخم پای دیابتی».
    found |= {" ".join(tokens[:i] + [t + "ی"] + tokens[i + 1:]) for i, t in enumerate(tokens)
              if t[-1] in "او" and len(t) >= 2}
    head = " ".join(tokens[:-1])
    if tokens[-1] in {"پایین", "کم"}:
        found |= {f"کاهش {head}", f"افت {head}", f"پایین بودن {head}"}
    if tokens[-1] in {"بالا", "زیاد"}:
        found |= {f"افزایش {head}", f"بالا بودن {head}", f"بالا رفتن {head}"}
    return found - {form}


def drug_monographs(snapshot, search):
    """concept id -> article id of the drug monograph named by one of its forms.

    query_topic lists clinical articles and often omits the monograph itself
    (sertraline -> SSRI articles only), so drugs are matched by name against
    every "<name>: Drug information" title of the snapshot catalog.
    """
    titles = sqlite3.connect((Path(snapshot) / "fts.db").resolve().as_uri() + "?mode=ro", uri=True)
    try:
        by_name = {}
        for article_id, title in titles.execute(
                "SELECT contentId, MIN(title) FROM fts WHERE type=1 AND contentId IS NOT NULL "
                "AND title LIKE '%: Drug information' GROUP BY contentId ORDER BY contentId"):
            name = title.rsplit(":", 1)[0]
            for variant in (name, _PAREN.sub("", name)):
                # "Amoxicillin and clavulanate" is searched as "amoxicillin clavulanate".
                for key in (normalize(variant), normalize(re.sub(r"\b(and|with)\b", " ", variant))):
                    by_name.setdefault(key, int(article_id))
    finally:
        titles.close()
    found = {}
    for concept_id, word, weight in search.execute("SELECT id, word, weight FROM query ORDER BY weight DESC"):
        if concept_id in found:
            continue
        for form in (normalize(word), normalize(_PAREN.sub("", word))):
            if form in by_name:
                found[concept_id] = by_name[form]
                break
    return found


_SALTS = re.compile(r"\b(sodium|potassium|calcium|magnesium|hydrochloride|hcl|sulfate|sulphate|"
                    r"acetate|maleate|citrate|phosphate|bromide|chloride|mesylate|tartrate|succinate|"
                    r"fumarate|besylate|hydrobromide|monohydrate|dihydrate|anhydrous|usp)\b")


def monograph_names(snapshot):
    """Normalized generic names of the snapshot's drug monographs: the title name,
    the name in parentheses ("Vitamin D3 (cholecalciferol)") and the name without
    its salt ("Megestrol acetate")."""
    titles = sqlite3.connect((Path(snapshot) / "fts.db").resolve().as_uri() + "?mode=ro", uri=True)
    try:
        names = set()
        for (title,) in titles.execute("SELECT DISTINCT title FROM fts WHERE type=1 AND title LIKE '%: Drug information'"):
            name = title.rsplit(":", 1)[0]
            for variant in [name, _PAREN.sub("", name), *re.findall(r"\(([^)]*)\)", name)]:
                names |= {normalize(variant), " ".join(_SALTS.sub(" ", normalize(variant)).split())}
        return names - {""}
    finally:
        titles.close()


def read_csv(name, directory=LEXICON_DIR):
    with (Path(directory) / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_optional(name, directory=LEXICON_DIR):
    return read_csv(name, directory) if (Path(directory) / name).exists() else []


def forms_of(value):
    return [form.strip().lstrip("+") for form in value.split("|") if form.strip().lstrip("+")]


def shared_forms(value):
    """Forms written «+form»: the Persian word names this concept too, but another
    row owns it (بی‌قراری is agitation and also restlessness)."""
    return [form.strip()[1:] for form in value.split("|") if form.strip().startswith("+")]


class ConceptLexicon:
    def __init__(self, concepts, forms, translit):
        self.concepts = concepts
        self.forms = forms
        self.translit = translit
        self._index_vocab()

    @classmethod
    def from_snapshot(cls, snapshot, directory=LEXICON_DIR, *, translit_threshold=0.8):
        search = sqlite3.connect((Path(snapshot) / "search.db").resolve().as_uri() + "?mode=ro", uri=True)
        try:
            drugs = drug_monographs(snapshot, search)
            concepts = {}
            for concept_id, *hits in search.execute(
                    "SELECT id, x_topic_hits, a_topic_hits, p_topic_hits, i_topic_hits FROM query_topic"):
                topics = {aud: [t for t in (h or "").split(",") if t] for aud, h in zip(AUDIENCES, hits)}
                kind = "drug" if concept_id in drugs else "condition"
                concepts[str(concept_id)] = Concept(str(concept_id), kind, 0, "", topics)
            forms = defaultdict(list)
            for concept_id, word, weight in search.execute("SELECT id, word, weight FROM query"):
                concept = concepts.get(str(concept_id))
                if concept is None:
                    continue
                if weight > concept.weight:
                    concept.weight, concept.label = weight, word
                entry = Entry("c:" + concept.concept_id, "subject", concept.kind, "search.db")
                for form in {normalize(word), normalize(_PAREN.sub("", word))}:
                    if form:
                        forms[form].append((weight, entry))
        finally:
            search.close()
        # Heaviest UpToDate concept first for a shared English surface form.
        forms = {form: [entry for _, entry in sorted(items, key=lambda item: -item[0])]
                 for form, items in forms.items()}
        lexicon = cls(concepts, forms, {})
        lexicon.generic_names = monograph_names(snapshot)
        lexicon._add_local(directory)
        lexicon._build_translit(translit_threshold)
        return lexicon

    def _put(self, form, entry, *, first, under_terms=False):
        for key in {normalize(form), normalize(form).replace(" ", "") if is_persian(form) else ""}:
            if not key:
                continue
            existing = [e for e in self.forms.get(key, []) if e != entry]
            lead = [e for e in existing if e.source == "terms"] if under_terms else []
            rest = [e for e in existing if e not in lead]
            self.forms[key] = lead + [entry] + rest if first else existing + [entry]

    def _add_local(self, directory):
        by_label = defaultdict(list)
        for concept in self.concepts.values():
            by_label[concept.label].append(concept)
        for row in read_csv("terms.csv", directory):
            if row["role"] not in ROLES:
                raise ValueError(f"Unknown role in terms.csv: {row['role']}")
            entry = Entry(f"{row['role']}:{row['key']}", row["role"], "term", "terms", row["status"])
            for form in forms_of(row["forms"]):
                # Query vocabulary outranks an UpToDate concept with the same
                # surface form ("kidney" is a context, not a topic request).
                self._put(form, entry, first=True)
        self.market = set()  # drugs the project lists: the Iranian market
        for row in read_csv("drugs_fa.csv", directory):
            if row["status"] == "unmatched":
                continue
            entry = Entry(row["key"], "subject", "drug", "drugs_fa", row["status"])
            self._put(row["fa"], entry, first=True, under_terms=True)
            self.market.add(row["key"])
        # Curated rows go last so they outrank a generated drug name ("اوره"
        # is the lab test before the urea cream). Under query vocabulary they
        # are a second reading: «نارسایی کبد» stays the liver context.
        curated = []
        for row in read_csv("concepts_fa.csv", directory):
            if row["kind"] not in KINDS:
                raise ValueError(f"Unknown kind in concepts_fa.csv: {row['kind']}")
            entry = Entry(self.concept_key(row["en"]), "subject", row["kind"], "concepts_fa", row["status"])
            shared = set(shared_forms(row["fa"]))
            for form in forms_of(row["fa"]):
                if form in shared:
                    continue
                self._put(form, entry, first=True, under_terms=True)
                curated.append((normalize(form), entry))
            for form in shared:
                self._put(form, Entry(entry.key, "subject", row["kind"], "concepts_fa", "shared"), first=False)
            if row["kind"] == "drug":
                self.market.add(entry.key)
        for form, entry in curated:
            for variant in phrase_variants(form):
                if variant not in self.forms:
                    self._put(variant, entry, first=True)
        self.stems = [(normalize(row["fa"]), row["position"]) for row in read_optional("drug_stems.csv", directory)]
        self.disambiguation = defaultdict(list)
        for row in read_optional("disambiguation.csv", directory):
            self.disambiguation[normalize(row["form"])].append(
                ([normalize(h) for h in forms_of(row["helpers"])], self.concept_key(row["en"])))
        # Ordinary Persian words never go to transliteration (نادر is not Toradol).
        common = Entry("stop:common_fa", "stop", "term", "common_fa", "proposed")
        path = Path(directory) / "common_fa.txt"
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else ()
        for word in (w for line in lines if not line.startswith("#") for w in line.split()):
            if normalize(word) and normalize(word) not in self.forms:
                self.forms[normalize(word)] = [common]
        self._index_vocab()

    def _index_vocab(self):
        self.vocab = {token for form in self.forms for token in form.split()}
        self.folded = defaultdict(set)
        for token in self.vocab:
            if is_persian(token):
                self.folded[token.translate(_HOMOPHONES)].add(token)

    def concept_key(self, english):
        entries = [e for e in self.forms.get(normalize(english), []) if e.source == "search.db"]
        if not entries:
            raise ValueError(f"No UpToDate concept for {english!r}")
        return entries[0].key

    def _build_translit(self, threshold):
        self.translit_threshold = threshold
        generic_names = self.__dict__.get("generic_names", set())
        generics = defaultdict(set)  # concept key -> generic names of the concept
        for form, entries in self.forms.items():
            if form in generic_names:
                for e in entries:
                    if e.source == "search.db" and e.kind == "drug":
                        generics[e.key].add(form)

        def generic(form, key):
            # A misspelling (megastrol), an ester or salt (mycophenolate mofetil) or
            # a qualified name (insulin isophane) of the generic name is not a brand
            # (Plavix). A drug whose generic name is unknown gets no brand penalty.
            if form in generic_names or not generics[key]:
                return True
            letters = letters_en(form)
            return any(form.split()[0] == g.split()[0]
                       or similarity(consonants(letters), consonants(letters_en(g)), 0.8) >= 0.8
                       for g in generics[key])

        drugs, conditions = defaultdict(list), defaultdict(list)
        for form, entries in self.forms.items():
            if is_persian(form):
                continue
            found = [e for e in entries if e.source == "search.db"]
            drug = [e for e in found if e.kind == "drug"]
            if drug:
                index, full, entry = drugs, letters_en(form), drug[0]
                entry = (entry, generic(form, entry.key))
            elif (found and " " not in form and len(form) >= CONDITION_MIN_LETTERS
                  and self.concepts[found[0].key[2:]].weight >= CONDITION_MIN_WEIGHT):
                index, full, entry = conditions, letters_en(form, french=True), (found[0], True)
            else:
                continue
            key = consonants(full)
            if len(key) >= 3:
                index[key[0]].append((key, full, form, entry))
        self.translit, self.translit_conditions = drugs, conditions

    def transliterate(self, text, *, conditions=False, context=False, known=False):
        """(score, form, entry, reason, alternatives) of the best candidate that
        clears its own threshold, or None. `context`: the query talks about a
        drug. `known`: the word occurs inside lexicon phrases, so it is Persian."""
        candidates = self._candidates(text, conditions)
        base = CONDITION_TRANSLIT if conditions else self.translit_threshold
        floor = base
        if len(text.replace(" ", "")) <= SHORT_WORD_LETTERS:
            floor = max(floor, SHORT_WORD_TRANSLIT)
        if known:
            floor = max(floor, VOCAB_TRANSLIT)
        stem = any(text.endswith(s) if pos == "suffix" else text.startswith(s) for s, pos in self.__dict__.get("stems", ()))
        passed = []
        for score, form, entry, weight, generic in candidates:
            threshold, why = base, []
            if not conditions:
                trusted = True
                if not generic:
                    threshold += BRAND_PENALTY
                    why.append("brand")
                    trusted = False
                if entry.key not in self.__dict__.get("market", ()):
                    threshold += OFF_MARKET_PENALTY
                    why.append("off-market")
                    trusted = False
                if stem:
                    why.append("stem")
                elif not trusted:  # a generic name on the Iranian market needs no stem
                    threshold += NO_STEM_PENALTY
                if context:
                    threshold -= CONTEXT_BONUS
                    why.append("context")
                threshold = min(max(threshold, base), MAX_TRANSLIT)
            if score >= max(threshold, floor):
                passed.append((score, weight, form, entry, ",".join(why)))
        if not passed:
            return None
        score, _, form, entry, why = max(passed, key=lambda p: (p[0], p[1]))
        others = tuple((c[2].key, c[0]) for c in candidates if c[2].key != entry.key)[:2]
        kind = "condition" if conditions else "drug"
        return score, form, Entry(entry.key, "subject", kind, "translit", "auto"), why, others

    def _candidates(self, text, conditions):
        cache = self.__dict__.setdefault("_translit_cache", {})
        if (text, conditions) not in cache:
            cache[text, conditions] = self._score_candidates(text, conditions)
        return cache[text, conditions]

    def _score_candidates(self, text, conditions):
        """Best few (score, form, entry, weight, generic) per concept above the lowest threshold."""
        full = letters_fa(text)
        key = consonants(full)
        if len(key) < 3:
            return []
        lowest = CONDITION_TRANSLIT if conditions else self.translit_threshold
        # The average of two similarities reaches the threshold only if the
        # skeleton alone reaches 2 * threshold - 1; cheaper candidates stop early.
        floor = 2 * lowest - 1
        best = {}
        index = self.translit_conditions if conditions else self.translit
        for candidate, candidate_full, form, (entry, generic) in index.get(key[0], ()):
            if abs(len(candidate) - len(key)) > 2:
                continue
            skeleton = similarity(key, candidate, floor)
            if not skeleton:
                continue
            score = (skeleton + similarity(full, candidate_full)) / 2
            if score < lowest:
                continue
            weight = self.concepts[entry.key[2:]].weight
            rank = (score, generic, weight)  # per concept: its closest form, the generic name on a tie
            if entry.key not in best or rank > best[entry.key][0]:
                best[entry.key] = (rank, (score, form, entry, weight, generic))
        return [row for _, row in sorted(best.values(), key=lambda r: (-r[0][0], -r[0][2]))][:5]

    def _entries(self, text, length):
        found = self.forms.get(text)
        # «فشارخون» is «فشار خون», but «و با» is not «وبا» (cholera).
        if not found and length > 1 and is_persian(text) and not any(map(self._is_stop, text.split())):
            found = self.forms.get(text.replace(" ", ""))
        return found

    def _is_stop(self, token):
        entries = self.forms.get(token)
        return bool(entries) and entries[0].role == "stop"

    def _lookup(self, tokens, i, *, terms_only=False, gapped=False):
        for length in range(min(MAX_SPAN, len(tokens) - i), 0, -1):
            text = " ".join(tokens[i:i + length])
            entries = self._entries(text, length)
            if entries and terms_only:
                entries = [e for e in entries if e.role != "subject"]
            if entries:
                return Span(i, i + length, text, tuple(entries))
            if gapped and length >= 3:
                # A severity word inside a subject phrase does not break it.
                gaps = tuple(j for j in range(i + 1, i + length - 1) if self._is_modifier(tokens[j]))
                if 0 < len(gaps) <= MAX_GAPS:
                    kept = [tokens[j] for j in range(i, i + length) if j not in gaps]
                    entries = self._entries(" ".join(kept), len(kept))
                    if entries and entries[0].role == "subject":
                        return Span(i, i + length, text, tuple(entries), gaps=gaps)
        return None

    def _is_modifier(self, token):
        entries = self.forms.get(token)
        return bool(entries) and entries[0].key in _MODIFIER_KEYS

    def _terms_within(self, tokens, span):
        found, i = [], span.start
        while i < span.end:
            inner = self._lookup(tokens[:span.end], i, terms_only=True)
            if inner:
                found.append(inner)
                i = inner.end
            else:
                i += 1
        return found

    def stem(self, token):
        """A known word for an unknown Persian one: missing madda (انتی بیوتیک) or a
        joined suffix (عفونتهای, دیابتی). Known words are kept, so «اسم» in
        «اسم تجاری» stays "name" and never becomes «آسم»."""
        return self._stem(token)[0]

    def _stem(self, token):
        if token in self.vocab or not is_persian(token):
            return token, ""
        variants = [token] + (["آ" + token[1:]] if token.startswith("ا") else [])
        for variant in variants:
            if variant in self.vocab:
                return variant, "madda"
            for suffix in _SUFFIXES:
                stem = variant[:-len(suffix)]
                if variant.endswith(suffix) and len(stem) >= 2 and stem in self.vocab:
                    return stem, "suffix"
        respelt = self._respell(token)
        return respelt, "homophone" if respelt != token else ""

    def _respell(self, token):
        """The one known word that sounds the same as a misspelt unknown word."""
        same = self.folded.get(token.translate(_HOMOPHONES), set())
        return next(iter(same)) if len(same) == 1 else token

    def tag(self, query):
        tokens, seg_end, respelled = [], [], []
        for segment in _SEGMENT.split(query or ""):
            words = normalize(segment).split()
            end = len(tokens) + len(words)
            for word in words:
                token, how = self._stem(word)
                if how == "homophone":
                    respelled.append((word, token))
                tokens.append(token)
                seg_end.append(end)
        tokens = tuple(tokens)
        spans, embedded, unknown, i = [], [], [], 0
        while i < len(tokens):
            span = self._lookup(tokens[:seg_end[i]], i, gapped=True)
            if span is None:
                unknown.append(i)
                i += 1
                continue
            if span.entries[0].source == "search.db" and span.end - span.start > 1:
                inner = self._terms_within(tokens, span)
                if sum(s.end - s.start for s in inner) == span.end - span.start:
                    # e.g. "renal dose": UpToDate stores it as a concept, but
                    # every word is query vocabulary, so it is not a subject.
                    spans.extend(inner)
                    i = span.end
                    continue
                embedded.extend(inner)
            embedded.extend(filter(None, (self._lookup(tokens[:g + 1], g, terms_only=True) for g in span.gaps)))
            spans.append(span)
            i = span.end
        # Unknown Persian words: try transliterated drug names, longest first,
        # then (only when nothing else is the subject) disease names. A run never
        # crosses punctuation and holds Persian words only («سرم > 1000» is no name).
        context = any(span.entries[0].key in DRUG_CONTEXT or span.entries[0].role in {"form", "route"}
                      for span in spans + embedded)
        # A common word is never a name on its own, but it may be half of a drug
        # name typed with a space («مونته لوکاست»).
        common = {span.start for span in spans if span.entries[0].source == "common_fa"}
        candidates = set(unknown) | common
        resolved = set()
        for start in sorted(candidates):
            if start in resolved or not is_persian(tokens[start]):
                continue
            for length in (3, 2, 1):
                run = list(range(start, start + length))
                if (start + length > seg_end[start] or any(j not in candidates or j in resolved for j in run)
                        or not all(is_persian(tokens[j]) for j in run) or all(j in common for j in run)):
                    continue
                text = " ".join(tokens[j] for j in run)
                # A word met inside lexicon phrases is Persian; only a near-exact
                # drug name may override that (پنتوپرازول, not «عروقی»).
                hit = self.transliterate(text, context=context,
                                         known=any(tokens[j] in self.vocab and j not in common for j in run))
                if hit:
                    spans = [span for span in spans if span.start not in common or span.start not in run]
                    spans.append(Span(start, start + length, text, (hit[2],), hit[0], reason=hit[3],
                                      alternatives=hit[4]))
                    resolved.update(run)
                    break
        if not any(span.entries[0].role == "subject" for span in spans):
            for start in unknown:
                token = tokens[start]
                if start in resolved or not is_persian(token) or len(token) < CONDITION_MIN_LETTERS:
                    continue
                hit = self.transliterate(token, conditions=True, known=token in self.vocab)
                if hit:
                    spans.append(Span(start, start + 1, token, (hit[2],), hit[0], alternatives=hit[4]))
                    resolved.add(start)
        spans = [self._disambiguate(span, tokens) for span in spans]
        spans.sort(key=lambda span: span.start)
        return Tagging(tokens, tuple(spans), tuple(tokens[j] for j in unknown if j not in resolved),
                       tuple(embedded), tuple(respelled))

    def _disambiguate(self, span, tokens):
        """A word that means two things takes the meaning its neighbours point to
        («بی‌قراری» next to an antipsychotic is akathisia)."""
        rules = self.disambiguation.get(span.text) if hasattr(self, "disambiguation") else None
        if not rules:
            return span
        text = " " + " ".join(tokens) + " "
        for helpers, key in rules:
            if any(f" {h} " in text for h in helpers):
                winner = Entry(key, "subject", "condition", "disambiguation", "resolved")
                return replace(span, entries=(winner,) + tuple(e for e in span.entries if e.key != key))
        return span


def build_drug_lexicon(pipeline_db, snapshot):
    """Map project Persian drug names (pipeline_v2) to UpToDate drug concepts."""
    salts = _SALTS
    search = sqlite3.connect((Path(snapshot) / "search.db").resolve().as_uri() + "?mode=ro", uri=True)
    pipeline = sqlite3.connect(Path(pipeline_db).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        drug_concepts = drug_monographs(snapshot, search)
        by_word = defaultdict(list)
        for concept_id, word, weight in search.execute("SELECT id, word, weight FROM query"):
            if concept_id in drug_concepts:
                by_word[normalize(word)].append((weight, concept_id))
        rows = []
        for english, persian in pipeline.execute(
                "SELECT ingredient_name, ingredient_name_fa FROM ingredient_clinical_profiles "
                "WHERE ingredient_name_fa <> '' ORDER BY ingredient_name"):
            method, found = "exact", by_word.get(normalize(english))
            if not found:
                method, found = "salt_stripped", by_word.get(" ".join(salts.sub(" ", normalize(english)).split()))
            if not found:
                method, found = "parenthesis_stripped", by_word.get(normalize(_PAREN.sub("", english)))
            if found:
                concept_id = max(found)[1]
                rows.append({"fa": persian, "en": english, "key": f"c:{concept_id}",
                             "article_id": drug_concepts[concept_id], "method": method,
                             "status": "project" if method == "exact" else "needs_review"})
            else:
                rows.append({"fa": persian, "en": english, "key": "", "article_id": "",
                             "method": "none", "status": "unmatched"})
        return rows
    finally:
        search.close()
        pipeline.close()
