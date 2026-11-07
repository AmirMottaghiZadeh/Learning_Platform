"""Concept lexicon regressions on a tiny synthetic snapshot; no UpToDate data."""

import csv
from pathlib import Path
import sqlite3
import tempfile
import unittest

from apps.uptodate.search_concepts import (
    KINDS, LEXICON_DIR, ROLES, ConceptLexicon, Entry, phrase_variants, letters_en, letters_fa, normalize, similarity, skeleton_en,
    skeleton_fa,
)

TOPICS = {1: "Ceftriaxone: Drug information", 2: "Sertraline: Drug information",
          3: "Selective serotonin reuptake inhibitors", 4: "Overview of hypertension in adults",
          5: "Clopidogrel: Drug information", 6: "Atenolol: Drug information",
          7: "Alcohol (ethanol) intoxication", 8: "Kidney replacement therapy",
          9: "Metformin: Drug information", 10: "Urea: Drug information", 11: "Asthma in adults",
          12: "Anemia in adults", 13: "Kidney function tests", 14: "Acute pancreatitis", 15: "Acute diarrhea",
          16: "Community-acquired pneumonia", 17: "Hypotension in adults", 18: "Acute liver failure",
          19: "Hypokalemia", 20: "Cholera", 21: "Febrile seizures", 22: "Agitation", 23: "Akathisia"}
# concept id -> (forms with weights, ranked topics). Sertraline's ranking lacks
# its monograph, as in the real search.db.
CONCEPTS = {
    10: ([("ceftriaxone", 500), ("rocephin", 100)], "1"),
    11: ([("sertraline", 400)], "3"),
    12: ([("hypertension", 900), ("htn", 50)], "4"),
    13: ([("clopidogrel", 300), ("plavix", 400)], "5"),
    14: ([("atenolol", 200)], "6"),
    15: ([("ethanol", 900)], "7"),
    16: ([("renal dose", 80)], "8"),
    17: ([("kidney", 100)], "8"),
    18: ([("metformin", 300)], "9"),
    19: ([("metformin adverse effects", 60)], "9"),
    20: ([("asthma", 800)], "11"),
    21: ([("urea", 100)], "10"),
    22: ([("anemia", 700)], "12"),
    23: ([("blood urea nitrogen", 90)], "13"),
    24: ([("pancreatitis", 900)], "14"),
    25: ([("diarrhea", 900)], "15"),
    26: ([("pneumonia", 900)], "16"),
    27: ([("hypotension", 900)], "17"),
    28: ([("hepatic failure", 500)], "18"),
    29: ([("hypokalemia", 700)], "19"),
    30: ([("cholera", 500)], "20"),
    31: ([("febrile seizure", 500)], "21"),
    32: ([("agitation", 500)], "22"),
    33: ([("akathisia", 500)], "23"),
}


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class ConceptLexiconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        search = sqlite3.connect(root / "search.db")
        search.execute("CREATE TABLE topic (id INTEGER PRIMARY KEY, title TEXT)")
        search.execute("CREATE TABLE query (id INTEGER, word TEXT, weight INTEGER)")
        search.execute("CREATE TABLE query_topic (id INTEGER PRIMARY KEY, x_topic_hits TEXT, "
                       "a_topic_hits TEXT, p_topic_hits TEXT, i_topic_hits TEXT)")
        search.executemany("INSERT INTO topic VALUES (?, ?)", TOPICS.items())
        for concept, (forms, hits) in CONCEPTS.items():
            search.executemany("INSERT INTO query VALUES (?, ?, ?)", [(concept, w, n) for w, n in forms])
            search.execute("INSERT INTO query_topic VALUES (?, ?, ?, ?, ?)", (concept, hits, hits, hits, hits))
        search.commit()
        search.close()
        fts = sqlite3.connect(root / "fts.db")
        fts.execute("CREATE TABLE fts (contentId TEXT, title TEXT, type INTEGER)")
        fts.executemany("INSERT INTO fts VALUES (?, ?, 1)", [(str(k), t) for k, t in TOPICS.items()])
        fts.commit()
        fts.close()
        lexicon = root / "lexicon"
        lexicon.mkdir()
        write_csv(lexicon / "terms.csv", [
            {"key": "dosing", "role": "intent", "forms": "دوز|dose", "status": "proposed", "note": ""},
            {"key": "adverse", "role": "intent", "forms": "عوارض|adverse effects", "status": "proposed", "note": ""},
            {"key": "kidney", "role": "context", "forms": "کلیه|renal|kidney", "status": "proposed", "note": ""},
            {"key": "function", "role": "stop", "forms": "در|و|با|of", "status": "proposed", "note": ""},
            {"key": "brand", "role": "intent", "forms": "نام تجاری|اسم تجاری", "status": "proposed", "note": ""},
            {"key": "liver", "role": "context", "forms": "نارسایی کبد", "status": "proposed", "note": ""},
            {"key": "severe", "role": "context", "forms": "شدید", "status": "proposed", "note": ""},
            {"key": "common", "role": "stop", "forms": "نادر", "status": "proposed", "note": ""},
        ])
        write_csv(lexicon / "concepts_fa.csv", [
            {"fa": "فشار خون|پرفشاری خون", "en": "hypertension", "kind": "condition", "status": "proposed", "note": ""},
            {"fa": "آسم", "en": "asthma", "kind": "condition", "status": "proposed", "note": ""},
            {"fa": "آنمی|کم خونی", "en": "anemia", "kind": "condition", "status": "proposed", "note": ""},
            {"fa": "اوره", "en": "blood urea nitrogen", "kind": "test", "status": "proposed", "note": ""},
            {"fa": "اسهال", "en": "diarrhea", "kind": "condition", "status": "proposed", "note": ""},
            {"fa": "پنومونی", "en": "pneumonia", "kind": "condition", "status": "proposed", "note": ""},
            {"fa": "افت فشار خون", "en": "hypotension", "kind": "condition", "status": "proposed", "note": ""},
            {"fa": "نارسایی کبد", "en": "hepatic failure", "kind": "condition", "status": "proposed", "note": ""},
            {"fa": "پتاسیم پایین", "en": "hypokalemia", "kind": "condition", "status": "proposed", "note": ""},
            {"fa": "+کم خونی", "en": "hypotension", "kind": "condition", "status": "proposed", "note": ""},
            {"fa": "وبا", "en": "cholera", "kind": "condition", "status": "proposed", "note": ""},
            {"fa": "تشنج تب", "en": "febrile seizure", "kind": "condition", "status": "proposed", "note": ""},
            {"fa": "بی قراری", "en": "agitation", "kind": "condition", "status": "proposed", "note": ""},
            {"fa": "آکاتیزی", "en": "akathisia", "kind": "condition", "status": "proposed", "note": ""}])
        write_csv(lexicon / "disambiguation.csv", [
            {"form": "بی قراری", "helpers": "هالوپریدول|ضد جنون", "en": "akathisia", "note": ""}])
        write_csv(lexicon / "drug_stems.csv", [{"fa": "ولول", "en": "olol", "position": "suffix", "class": "beta blocker"}])
        (lexicon / "common_fa.txt").write_text("# ordinary words\nمیتونن نظر سفتری\n", encoding="utf-8")
        write_csv(lexicon / "drugs_fa.csv", [
            {"fa": "سفتریاکسون", "en": "ceftriaxone", "key": "c:10", "article_id": "1", "method": "exact",
             "status": "project"},
            {"fa": "اوره", "en": "urea", "key": "c:21", "article_id": "10", "method": "exact", "status": "project"}])
        cls.root, cls.lexicon_dir = root, lexicon
        cls.lexicon = ConceptLexicon.from_snapshot(root, lexicon)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_normalize_unifies_persian_spelling_digits_and_marks(self):
        self.assertEqual(normalize("دوزِ كلیه‌ای ۲٫۵ ميلي"), "دوز کلیه ای 2.5 میلی")
        self.assertEqual(normalize("CrCl <30"), "crcl < 30")
        self.assertEqual(normalize("سوء تغذیه"), "سو تغذیه")

    def test_normalize_drops_detached_plural_suffixes(self):
        self.assertEqual(normalize("عفونت‌های ادراری"), "عفونت ادراری")
        self.assertEqual(normalize("عفونت های ادراری"), "عفونت ادراری")

    def test_similarity_floor_only_cuts_hopeless_pairs(self):
        self.assertEqual(similarity("abcdef", "uvwxyz", 0.6), 0.0)
        self.assertEqual(similarity("sftriaksn", "sftriaksun", 0.6), similarity("sftriaksn", "sftriaksun"))

    def test_transliteration_skeleton_matches_latin_name(self):
        self.assertEqual(skeleton_fa("سفتریاکسون"), skeleton_en("ceftriaxone"))
        persian = letters_fa("آتنولول")
        self.assertGreater(similarity(persian, letters_en("atenolol")), similarity(persian, letters_en("ethanol")))

    def test_drug_is_recognised_by_monograph_name_even_if_ranking_omits_it(self):
        self.assertEqual(self.lexicon.concepts["11"].kind, "drug")
        self.assertEqual(self.lexicon.concepts["12"].kind, "condition")

    def test_persian_lexicon_and_joined_spelling(self):
        for query in ("درمان فشار خون", "فشارخون"):
            with self.subTest(query=query):
                self.assertEqual(self.lexicon.tag(query).keys("subject"), ["c:12"])

    def test_query_vocabulary_outranks_a_concept_with_the_same_form(self):
        tagging = self.lexicon.tag("kidney")
        self.assertEqual(tagging.keys("context"), ["context:kidney"])
        self.assertEqual(tagging.keys("subject"), [])

    def test_compound_concept_of_query_words_splits_into_terms(self):
        tagging = self.lexicon.tag("ceftriaxone renal dose")
        self.assertEqual(tagging.keys("subject"), ["c:10"])
        self.assertEqual(tagging.keys("intent"), ["intent:dosing"])
        self.assertEqual(tagging.keys("context"), ["context:kidney"])

    def test_mixed_compound_keeps_subject_and_exposes_intent(self):
        tagging = self.lexicon.tag("metformin adverse effects")
        self.assertEqual(tagging.keys("subject"), ["c:19"])
        self.assertEqual(tagging.keys("intent"), ["intent:adverse"])

    def test_unknown_persian_brand_and_misspelling_transliterate_to_drugs(self):
        self.assertEqual(self.lexicon.tag("عوارض پلاویکس").keys("subject"), ["c:13"])
        self.assertEqual(self.lexicon.tag("سرترالین").keys("subject"), ["c:11"])
        self.assertEqual(self.lexicon.tag("آتنولول").keys("subject"), ["c:14"])

    def test_plural_and_adjective_suffixes_reach_the_stem(self):
        for query in ("آسم‌ها", "آسمی", "آسمهای"):
            with self.subTest(query=query):
                self.assertEqual(self.lexicon.tag(query).keys("subject"), ["c:20"])

    def test_missing_madda_is_restored_only_for_unknown_words(self):
        self.assertEqual(self.lexicon.tag("درمان انمی").keys("subject"), ["c:22"])
        # «اسم» is a known word ("name"), so it is never read as «آسم».
        tagging = self.lexicon.tag("اسم تجاری سفتریاکسون")
        self.assertEqual(tagging.keys("intent"), ["intent:brand"])
        self.assertEqual(tagging.keys("subject"), ["c:10"])

    def test_same_sounding_misspelling_is_respelt_but_one_letter_off_is_not(self):
        self.assertEqual(self.lexicon.tag("درمان اسحال").keys("subject"), ["c:25"])  # ح for ه
        # One letter off can be another disease (هیپوپلازی/هیپرپلازی), so it stays unknown.
        self.assertEqual(self.lexicon.tag("سفتریاکسون در پنمونی").keys("subject"), ["c:10"])

    def test_curated_concept_outranks_generated_drug_name(self):
        self.assertEqual(self.lexicon.tag("اوره").keys("subject"), ["c:23"])

    def test_detached_affixes_do_not_break_a_phrase(self):
        self.assertEqual(normalize("قفسه‌ی سینه"), "قفسه سینه")
        self.assertEqual(normalize("شایع‌ترین عوارض"), "شایع عوارض")
        self.assertEqual(normalize("مصرف می‌شود"), "مصرف شود")

    def test_severity_word_inside_a_phrase_is_skipped_and_kept_as_context(self):
        tagging = self.lexicon.tag("افت شدید فشار خون")
        self.assertEqual(tagging.keys("subject"), ["c:27"])
        self.assertEqual(tagging.keys("context"), ["context:severe"])

    def test_context_phrase_also_names_its_concept(self):
        tagging = self.lexicon.tag("نارسایی کبد")
        self.assertEqual(tagging.keys("context"), ["context:liver"])
        self.assertEqual(tagging.keys("subject"), [])
        self.assertEqual(tagging.concepts(), ["c:28"])

    def test_level_phrase_gets_change_variants_but_not_the_reverse(self):
        self.assertEqual(self.lexicon.tag("کاهش پتاسیم").keys("subject"), ["c:29"])
        self.assertEqual(self.lexicon.tag("پتاسیم کم").keys("subject"), ["c:29"])
        self.assertEqual(phrase_variants("کاهش وزن"), set())  # weight loss is not «وزن پایین»

    def test_shared_word_keeps_one_subject_and_names_both_concepts(self):
        tagging = self.lexicon.tag("کم خونی")
        self.assertEqual(tagging.keys("subject"), ["c:22"])
        self.assertEqual(tagging.concepts(), ["c:22", "c:27"])

    def test_punctuation_ends_a_phrase(self):
        self.assertEqual(self.lexicon.tag("تشنج تب").keys("subject"), ["c:31"])
        self.assertNotIn("c:31", self.lexicon.tag("استفراغ، تشنج، تب").keys("subject"))

    def test_function_words_are_not_glued_into_a_name(self):
        self.assertEqual(self.lexicon.tag("وبا").keys("subject"), ["c:30"])
        self.assertEqual(self.lexicon.tag("تب و با سرفه").keys("subject"), [])  # «و با» is not «وبا»

    def test_neighbouring_words_choose_the_meaning_of_a_shared_word(self):
        self.assertEqual(self.lexicon.tag("بی قراری").keys("subject"), ["c:32"])
        tagging = self.lexicon.tag("بی قراری با هالوپریدول")
        self.assertEqual(tagging.keys("subject")[0], "c:33")
        self.assertTrue(tagging.interpretation()[0]["confirm"])

    def test_common_words_and_possessives(self):
        self.assertEqual(self.lexicon.tag("میتونن").keys("subject"), [])
        self.assertEqual(self.lexicon.tag("میتونن").keys("stop"), ["stop:common_fa"])
        self.assertEqual(self.lexicon.tag("آسمش").keys("subject"), ["c:20"])

    def test_a_common_word_may_be_half_of_a_spaced_drug_name(self):
        self.assertEqual(self.lexicon.tag("سفتری").keys("subject"), [])
        tagging = self.lexicon.tag("دوز سفتری اکسون")
        self.assertEqual(tagging.keys("subject"), ["c:10"])
        self.assertEqual(tagging.keys("stop"), [])

    def test_interpretation_flags_shared_words(self):
        item = self.lexicon.tag("کم خونی").interpretation()[0]
        self.assertEqual(item["key"], "c:22")
        self.assertTrue(item["confirm"])
        self.assertIn("c:27", [alt["key"] for alt in item["alternatives"]])

    def test_brand_and_off_market_candidates_need_a_closer_match(self):
        def best(word, score, form, key, generic, **kwargs):
            entry = Entry(key, "subject", "drug", "search.db", "proposed")
            self.lexicon.__dict__.setdefault("_translit_cache", {})[word, False] = [(score, form, entry, 400, generic)]
            return self.lexicon.transliterate(word, **kwargs)

        # Plavix is a brand of a drug not on the Iranian market, with no class stem: it needs 0.95.
        self.assertIsNone(best("پلاویکسی", 0.9, "plavix", "c:13", False))
        hit = best("پلاویکسی", 0.96, "plavix", "c:13", False)
        self.assertEqual((hit[2].key, hit[3]), ("c:13", "brand,off-market"))
        # A drug question lowers the bar a little.
        self.assertEqual(best("پلاویکسی", 0.93, "plavix", "c:13", False, context=True)[3], "brand,off-market,context")
        # A generic name on the market keeps the base threshold.
        self.assertEqual(best("سفتریاکسونی", 0.82, "ceftriaxone", "c:10", True)[2].key, "c:10")

    def test_persian_gz_spells_x(self):
        self.assertEqual(skeleton_fa("دگزامتازون"), skeleton_en("dexamethasone"))
        self.assertEqual(letters_fa("مونته لوکاست"), letters_fa("مونتلوکاست"))  # ه ends each word as -e

    def test_ezafe_after_a_vowel_is_a_variant(self):
        self.assertIn("ریزش موی", phrase_variants("ریزش مو"))

    def test_ordinary_short_word_is_not_read_as_a_drug(self):
        self.assertEqual(self.lexicon.tag("نادر").keys("subject"), [])

    def test_disease_name_transliterates_only_without_another_subject(self):
        tagging = self.lexicon.tag("درمان پانکراتیت")
        self.assertEqual(tagging.keys("subject"), ["c:24"])
        self.assertEqual(tagging.spans[-1].entries[0].kind, "condition")
        # With a known subject the unknown word is left alone.
        self.assertEqual(self.lexicon.tag("سفتریاکسون پانکراتیت").keys("subject"), ["c:10"])

    def test_ordinary_unknown_word_is_left_unknown(self):
        tagging = self.lexicon.tag("دوز سفتریاکسون در کلیه زززز")
        self.assertEqual(tagging.keys("subject"), ["c:10"])
        self.assertEqual(tagging.unknown, ("زززز",))

    def test_persian_entry_must_name_an_existing_concept(self):
        lexicon = Path(self.tmp.name) / "bad"
        lexicon.mkdir(exist_ok=True)
        for name in ("terms.csv", "drugs_fa.csv"):
            (lexicon / name).write_bytes((self.lexicon_dir / name).read_bytes())
        write_csv(lexicon / "concepts_fa.csv", [
            {"fa": "بیماری ساختگی", "en": "not a concept", "kind": "condition", "status": "proposed", "note": ""}])
        with self.assertRaisesRegex(ValueError, "No UpToDate concept"):
            ConceptLexicon.from_snapshot(self.root, lexicon)
        write_csv(lexicon / "concepts_fa.csv", [
            {"fa": "آسم", "en": "asthma", "kind": "disease", "status": "proposed", "note": ""}])
        with self.assertRaisesRegex(ValueError, "Unknown kind"):
            ConceptLexicon.from_snapshot(self.root, lexicon)


class LexiconFileTests(unittest.TestCase):
    def rows(self, name):
        with (LEXICON_DIR / name).open(encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_terms_have_known_roles_and_no_duplicate_forms(self):
        seen = {}
        for row in self.rows("terms.csv"):
            self.assertIn(row["role"], ROLES)
            for form in row["forms"].split("|"):
                key = normalize(form)
                self.assertIn(seen.get(key, row["key"]), {row["key"]}, f"{form!r} is in {seen.get(key)} and {row['key']}")
                seen[key] = row["key"]

    def test_monograph_sections_use_known_facets(self):
        keys = {row["key"] for row in self.rows("terms.csv")}
        for row in self.rows("monograph_sections.csv"):
            self.assertTrue(set(row["facet"].split("+")) <= keys, row["facet"])
            self.assertIn(row["population"], {"any", "adult", "pediatric", "neonate", "elderly"})

    def test_concept_rows_use_known_kinds_and_unique_persian_forms(self):
        seen = {}
        for row in self.rows("concepts_fa.csv"):
            self.assertIn(row["kind"], KINDS, row["en"])
            for form in row["fa"].split("|"):
                if form.startswith("+"):
                    continue  # a shared word names this concept too; another row owns it
                key = normalize(form)
                self.assertIn(seen.get(key, row["en"]), {row["en"]}, f"{form!r} is in {seen.get(key)} and {row['en']}")
                seen[key] = row["en"]

    def test_drug_rows_are_consistent(self):
        for row in self.rows("drugs_fa.csv"):
            self.assertIn(row["status"], {"project", "needs_review", "reviewed", "unmatched"})
            self.assertEqual(bool(row["key"]), row["status"] != "unmatched", row["en"])


if __name__ == "__main__":
    unittest.main()
