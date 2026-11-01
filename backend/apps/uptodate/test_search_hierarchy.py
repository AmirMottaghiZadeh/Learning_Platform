"""Article catalog, outline and passage-scope regressions with synthetic text.

Requested-depth routing is exercised in test_search_request.py.
"""

import unittest

from apps.uptodate.search_extraction import extract_article
from apps.uptodate.search_hierarchy import (
    ArticleCatalog, ArticleMetadata, HierarchicalRetriever, PassageScope,
    article_sections, local_passages,
)


def outline(*nodes):
    return "<ul>" + "".join(f'<li><a href="#{key}">{title}</a></li>' for key, title in nodes) + "</ul>"


class HierarchyTests(unittest.TestCase):
    def setUp(self):
        titles = {
            "mono": "Apixaban: Drug information",
            "peds": "Apixaban: Pediatric drug information",
            "patient": "Apixaban: Patient drug information",
            "hiv": "Drug interactions with antiretroviral agents for HIV",
            "hiv_general": "Treatment of HIV",
            "thyroid": "Drug interactions with thyroid hormones",
            "warfarin": "Warfarin: Drug information",
        }
        self.catalog = ArticleCatalog(ArticleMetadata.from_title(key, title) for key, title in titles.items())
        html = ('<div id="F1"><h2>Dosing: Kidney Impairment: Adult</h2>'
                '<p>Apixaban renal dose adjustment: synthetic adult reference passage.</p></div>'
                '<div id="F2"><h2>Dosing: Liver Impairment: Adult</h2>'
                '<p>Apixaban hepatic dose adjustment: synthetic liver reference passage.</p></div>'
                '<div id="F3"><h2>Dosing: Kidney Impairment: Pediatric</h2>'
                '<p>Apixaban kidney dose: synthetic pediatric reference passage.</p></div>')
        toc = outline(("F1", "Dosing: Kidney Impairment: Adult"),
                      ("F2", "Dosing: Liver Impairment: Adult"),
                      ("F3", "Dosing: Kidney Impairment: Pediatric"))
        self.content = {key: (extract_article(key, html), toc) for key in ("mono", "peds", "patient")}
        # Deliberately strong off-topic paragraph: it must never be read for a
        # single-drug dosing question, whatever its passage score.
        self.content["hiv"] = (extract_article("hiv", '<p>' + "Apixaban renal dose adjustment kidney disease " * 30 + '</p>'), "")
        self.content["warfarin"] = (extract_article("warfarin", "<p>Warfarin comparison with apixaban.</p>"), "")
        self.loads = []

    def load(self, key):
        self.loads.append(key)
        return self.content[key]

    def engine(self):
        return HierarchicalRetriever(self.catalog, self.load)

    def test_named_subject_is_required_even_when_generic_adjustment_scores_high(self):
        catalog = ArticleCatalog([
            ArticleMetadata.from_title("wrong", "Patient education: Adjustment disorder (The Basics)"),
            ArticleMetadata.from_title("right", "Insulin therapy in diabetes mellitus"),
            ArticleMetadata.from_title("nav", "Society guideline links: Insulin adjustment"),
        ])
        candidates = catalog.select(catalog.plan("insulin adjustment during illness"))
        self.assertEqual([candidate.article.article_id for candidate in candidates], ["right"])

    def test_action_words_alone_do_not_identify_a_source(self):
        self.assertEqual(self.catalog.select(self.catalog.plan("initial treatment adjustment")), ())

    def test_bleeding_management_can_prioritize_a_clinical_article_over_monograph(self):
        articles = list(self.catalog.articles) + [
            ArticleMetadata.from_title("bleed", "Management of bleeding with oral anticoagulants")]
        catalog = ArticleCatalog(articles)
        selected = catalog.select(catalog.plan("management of major bleeding with apixaban"))
        self.assertEqual(selected[0].article.article_id, "bleed")
        self.assertIn("mono", [c.article.article_id for c in selected])

    def test_pregnancy_context_excludes_general_hypertension_article(self):
        catalog = ArticleCatalog([
            ArticleMetadata.from_title("preg", "Treatment of hypertension in pregnant patients"),
            ArticleMetadata.from_title("general", "Treatment of severe hypertension"),
        ])
        self.assertEqual([c.article.article_id for c in catalog.select(
            catalog.plan("treatment of severe hypertension in pregnancy"))], ["preg"])

    def test_interaction_context_keeps_hiv_article_and_excludes_generic_interactions(self):
        selected = self.catalog.select(self.catalog.plan("apixaban interactions with HIV treatment"))
        self.assertEqual({c.article.article_id for c in selected}, {"mono", "hiv"})

    def test_single_drug_dosing_reads_only_the_monograph(self):
        for query in ("apixaban dose adjustment in kidney disease", "تنظیم دوز آپیکسابان در نارسایی کلیوی"):
            with self.subTest(query=query):
                self.loads.clear()
                result = self.engine().search(query)
                self.assertEqual(self.loads, ["mono"])
                self.assertEqual(result["items"][0]["destination"], {"article_id": "mono", "section_id": "F1"})

    def test_pediatric_query_uses_pediatric_monograph_and_section(self):
        result = self.engine().search("apixaban renal dose in children")
        self.assertEqual(self.loads, ["peds"])
        self.assertEqual(result["items"][0]["destination"], {"article_id": "peds", "section_id": "F3"})

    def test_no_body_is_read_when_no_article_matches(self):
        result = self.engine().search("zzzzunknownzzzz")
        self.assertEqual(result["status"], "no_article_candidate")
        self.assertEqual(self.loads, [])

    def test_entity_matching_uses_whole_tokens_and_longest_name(self):
        catalog = ArticleCatalog([ArticleMetadata.from_title("a", "Drug A: Drug information"),
                                  ArticleMetadata.from_title("ab", "Drug A B: Drug information")], aliases={})
        self.assertEqual(catalog.plan("drug a b dose").entities, ("drug a b",))
        self.assertEqual(self.catalog.plan("apixabanlike").entities, ())

    def test_unknown_seed_entity_is_not_invented_in_missing_snapshot(self):
        catalog = ArticleCatalog([ArticleMetadata.from_title("w", "Warfarin: Drug information")])
        self.assertEqual(catalog.plan("دوز آپیکسابان").entities, ())

    def test_outline_preserves_full_parent_path_and_deduplicates_shortcut(self):
        html = ('<div id="topicText"><p class="headingAnchor" id="H2">Kidney impairment</p>'
                '<p>Apixaban renal dose.</p></div>')
        toc = ('<ul><li><a href="#H2">Shortcut</a></li><li>'
               '<a onclick="doOperation({sectionName:&quot;H1&quot;})">Dosing</a>'
               '<ul><li><a href="#H2">Kidney impairment</a></li></ul></li></ul>')
        article = extract_article("mono", html)
        sections = article_sections(toc, article)
        leaf = next(s for s in sections if s.section_id == "H2")
        self.assertEqual(leaf.path_ids, ("H1", "H2"))
        self.assertEqual(leaf.path_titles, ("Dosing", "Kidney impairment"))
        self.assertEqual(len([s for s in sections if s.section_id == "H2"]), 1)
        self.content["mono"] = (article, toc)
        result = self.engine().search("apixaban renal dose")
        self.assertEqual(result["sections"][0]["section_path"], ["H1", "H2"])

    def test_missing_outline_has_explicit_flat_provenance(self):
        article, _ = self.content["mono"]
        sections = article_sections("", article)
        self.assertTrue(all(s.provenance == "body_heading_only" for s in sections))
        self.assertTrue(all(len(s.path_ids) == 1 for s in sections))

    def test_loader_cannot_substitute_article(self):
        engine = HierarchicalRetriever(self.catalog, lambda key: self.content["hiv"])
        with self.assertRaisesRegex(ValueError, "different article"):
            engine.search("apixaban renal dose")

    def test_alias_dictionary_rejects_ambiguous_or_malformed_names(self):
        articles = self.catalog.articles
        for aliases in ({"apixaban": "wrong string"}, {"apixaban": [None]},
                        {"apixaban": ["same"], "warfarin": ["same"]}):
            with self.subTest(aliases=aliases), self.assertRaises(ValueError):
                ArticleCatalog(articles, aliases=aliases)

    def test_empty_or_unversioned_scope_fails_closed(self):
        for scope in (PassageScope("", "hash", "v4", ("F1",)), PassageScope("mono", "", "v4", None),
                      PassageScope("mono", "hash", "", None), PassageScope("mono", "hash", "v4", ()),
                      PassageScope("mono", "hash", "v4", ("F1",), ())):
            with self.subTest(scope=scope), self.assertRaises(ValueError):
                scope.validate()

    def test_local_backend_rejects_stale_revision(self):
        article, _ = self.content["mono"]
        scope = PassageScope("mono", "different", article.version, ("F1",))
        with self.assertRaisesRegex(ValueError, "revision"):
            local_passages(self.catalog.plan("apixaban"), article, scope, 10)

    def test_invalid_query_or_search_bounds_are_rejected(self):
        for query in ("", "   ", "a" * 2001):
            with self.subTest(query=query[:10]), self.assertRaises(ValueError):
                self.engine().search(query)
        for kwargs in ({"article_beam": 0}, {"section_beam": 0}, {"limit": 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.engine().search("apixaban", **kwargs)


if __name__ == "__main__":
    unittest.main()
