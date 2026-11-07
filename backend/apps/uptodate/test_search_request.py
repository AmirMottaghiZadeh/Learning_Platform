"""Requested-depth routing with synthetic text, not medical recommendations."""

import re
import unittest
from unittest.mock import Mock

from apps.uptodate.search_extraction import extract_article
from apps.uptodate.search_hierarchy import ArticleCatalog, ArticleMetadata, HierarchicalRetriever, local_passages
from apps.uptodate.search_request import measurements, route_constraints


class RequestedDepthTests(unittest.TestCase):
    def setUp(self):
        titles = {"a": "Apixaban: Drug information", "t": "Testmed: Drug information",
                  "p": "Apixaban: Pediatric drug information", "w": "Warfarin: Drug information",
                  "h": "HIV treatment", "c": "Evaluation of synthetic anemia"}
        self.catalog = ArticleCatalog((ArticleMetadata.from_title(key, value) for key, value in titles.items()),
                                     aliases={"apixaban": ["آپیکسابان"], "testmed": ["تستمد"]})
        # Testmed and all its text are invented solely to exercise positive
        # route matching; no route/dose assertion about apixaban is made.
        outline = ('<ul><li><a href="#D">Dosing</a><ul>'
                   '<li><a href="#R">Kidney impairment: Adult</a><ul>'
                   '<li><a href="#B">IV bolus</a></li></ul></li>'
                   '<li><a href="#L">Liver impairment: Adult</a></li></ul></li>'
                   '<li><a href="#A">Administration</a></li>'
                   '<li><a href="#F">Formulations</a></li></ul>')
        apixaban = ('<h2 id="R">Dosing: Kidney impairment: Adult</h2>'
                    '<p>Oral synthetic reference 2.5 mg.</p>'
                    '<p>Oral synthetic reference 5 mg.</p>'
                    '<h2 id="L">Dosing: Liver impairment: Adult</h2>'
                    '<p>Unrelated IV bolus label 2.5 mg.</p>')
        synthetic = ('<h2 id="R">Kidney impairment: Adult</h2>'
                     '<p>Synthetic IV bolus label 5 mg. Hemodialysis reference.</p>'
                     '<p>Synthetic IV infusion label; separate oral bolus label.</p>'
                     '<p>Synthetic IV bolus label 5 mcg.</p>'
                     '<p>Synthetic IV bolus label below threshold &lt;30 ml/min.</p>'
                     '<h3 id="B">IV bolus</h3><p>Other synthetic label 7 mg.</p>'
                     '<h2 id="L">Liver impairment: Adult</h2><p>IV bolus label 5 mg.</p>'
                     '<h3 id="X">Hemodialysis</h3><p>Liver-only heading distractor.</p>'
                     '<h2 id="A">Administration</h2><p>Synthetic IV bolus route label.</p>'
                     '<h2 id="F">Formulations</h2><p>Synthetic BrandQ product label.</p>')
        def anchored(html):
            return re.sub(r'<h[23] id="([^"]+)">([^<]+)</h[23]>',
                          r'<p class="headingAnchor" id="\1">\2</p>', html)
        self.content = {
            "a": (extract_article("a", anchored(apixaban)), outline),
            "t": (extract_article("t", anchored(synthetic)), outline.replace(
                '<li><a href="#L">Liver impairment: Adult</a></li>',
                '<li><a href="#L">Liver impairment: Adult</a><ul><li><a href="#X">Hemodialysis</a></li></ul></li>')),
            "p": (extract_article("p", anchored('<h2 id="P">Dosing: Kidney impairment: Pediatric</h2><p>Child reference.</p>')), ""),
        }
        self.loader = Mock(side_effect=lambda key: self.content[key])
        self.backend = Mock(side_effect=local_passages)
        self.engine = HierarchicalRetriever(self.catalog, self.loader, self.backend)

    def test_drug_title_stops_before_body_or_passages(self):
        for query in ("apixaban", "آپیکسابان", "apixaban drug information"):
            with self.subTest(query=query):
                result = self.engine.search(query)
                self.assertEqual(result["result_level"], "article")
                self.assertEqual(result["items"][0]["destination"], {"article_id": "a"})
                self.assertEqual(result["sections"], [])
                self.assertEqual(result["paragraphs"], [])
        self.loader.assert_not_called()
        self.backend.assert_not_called()

    def test_exact_clinical_title_is_also_an_article_destination(self):
        result = self.engine.search("Evaluation of synthetic anemia")
        self.assertEqual(result["items"][0]["destination"], {"article_id": "c"})
        self.loader.assert_not_called()

    def test_comparison_keeps_both_article_destinations(self):
        result = self.engine.search("compare apixaban and warfarin", article_beam=1)
        self.assertEqual({item["article_id"] for item in result["items"]}, {"a", "w"})
        self.assertTrue(all(item["kind"] == "article" for item in result["items"]))
        self.loader.assert_not_called()

    def test_renal_request_returns_section_without_searching_passages(self):
        for query in ("apixaban renal dose adjustment", "تنظیم دوز کلیوی در آپیکسابان"):
            with self.subTest(query=query):
                result = self.engine.search(query)
                self.assertEqual(result["result_level"], "section")
                self.assertEqual(result["items"][0]["destination"], {"article_id": "a", "section_id": "R"})
                self.assertEqual(result["sections"][0]["section_path"], ["D", "R"])
                self.assertEqual(result["paragraphs"], [])
        self.backend.assert_not_called()
        self.assertEqual({call.args[0] for call in self.loader.call_args_list}, {"a"})

    def test_pediatric_population_remains_in_requested_section(self):
        result = self.engine.search("apixaban renal dose children")
        self.assertEqual(result["items"][0]["destination"], {"article_id": "p", "section_id": "P"})
        self.backend.assert_not_called()

    def test_broad_section_request_stops_at_parent(self):
        result = self.engine.search("testmed dose")
        self.assertEqual([item["section_id"] for item in result["items"]], ["D"])
        self.backend.assert_not_called()

    def test_missing_section_never_broadens_to_article_body(self):
        result = self.engine.search("apixaban pregnancy")
        self.assertEqual(result["result_level"], "section")
        self.assertEqual(result["status"], "no_section_match")
        self.assertEqual(result["items"], [])
        self.backend.assert_not_called()

    def test_unknown_heading_remains_unmatched_section(self):
        result = self.engine.search("apixaban Zzzheading")
        self.assertEqual(result["result_level"], "section")
        self.assertEqual(result["status"], "no_section_match")
        self.backend.assert_not_called()

    def test_absent_route_under_renal_section_cannot_use_other_section_or_hiv(self):
        for query in ("apixaban renal dose product IV bolus",
                      "تنظیم دوز آپیکسابان در بیماری کلیوی در محصول iv bolus"):
            with self.subTest(query=query):
                result = self.engine.search(query)
                self.assertEqual(result["result_level"], "paragraph")
                self.assertEqual(result["status"], "no_paragraph_match")
                self.assertEqual(result["articles"][0]["stop_reason"], "no_paragraph_satisfies_details")
                self.assertEqual(result["items"], [])
        self.backend.assert_not_called()
        self.assertEqual({call.args[0] for call in self.loader.call_args_list}, {"a"})

    def test_positive_route_product_request_is_prefiltered_within_actual_section(self):
        result = self.engine.search("testmed renal dose product IV bolus")
        self.assertEqual(result["result_level"], "paragraph")
        self.assertTrue(result["paragraphs"])
        self.assertEqual({hit["section_id"] for hit in result["paragraphs"]}, {"R", "B"})
        scope = self.backend.call_args.args[2]
        article = self.content["t"][0]
        allowed_texts = [block.text for block in article.blocks if block.paragraph_id in scope.paragraph_ids]
        self.assertTrue(all("infusion" not in text for text in allowed_texts))
        self.assertEqual(result["plan"]["request"]["section_terms"], ["dose", "kidney"])
        self.assertEqual(set(result["plan"]["request"]["routes"]), {"iv", "bolus"})

    def test_qualifier_in_descendant_heading_is_inherited(self):
        result = self.engine.search("testmed renal dose IV bolus 7 mg")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["section_id"], "B")
        self.assertEqual(result["items"][0]["section_path"], ["D", "R", "B"])

    def test_heading_word_elsewhere_does_not_redirect_requested_branch(self):
        result = self.engine.search("testmed renal dose hemodialysis")
        self.assertEqual(result["result_level"], "paragraph")
        self.assertEqual({item["section_id"] for item in result["items"]}, {"R"})
        self.assertEqual(result["plan"]["request"]["paragraph_terms"], ["hemodialysis"])

    def test_numeric_detail_matches_value_and_unit_together(self):
        for query, count in (("testmed renal dose IV bolus 5 mg", 1),
                             ("testmed renal dose IV bolus 5 mcg", 1),
                             ("testmed renal dose IV bolus 50 mg", 0),
                             ("testmed renal dose IV bolus <30 ml/min", 1),
                             ("testmed renal dose IV bolus >30 ml/min", 0)):
            with self.subTest(query=query):
                result = self.engine.search(query)
                self.assertEqual(len(result["items"]), count)

    def test_realistic_numeric_qualifier_on_apixaban_has_only_matching_block(self):
        result = self.engine.search("apixaban renal dose 2.5 mg")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["section_id"], "R")
        self.assertEqual(result["result_level"], "paragraph")

    def test_route_only_request_selects_administration_before_paragraph(self):
        result = self.engine.search("testmed IV bolus")
        self.assertEqual({item["section_id"] for item in result["items"]}, {"A"})

    def test_unknown_product_is_no_match(self):
        result = self.engine.search("testmed renal dose product Zzzbrand")
        self.assertEqual(result["status"], "no_paragraph_match")
        self.backend.assert_not_called()

    def test_product_only_request_selects_formulation_section(self):
        result = self.engine.search("testmed product BrandQ")
        self.assertEqual({item["section_id"] for item in result["items"]}, {"F"})

    def test_backend_cannot_escape_even_to_another_paragraph_in_selected_section(self):
        def malicious(plan, article, scope, limit):
            good = local_passages(plan, article, scope, limit)[0]
            wrong = next(block for block in article.blocks if block.section_id == "R"
                         and block.paragraph_id not in scope.paragraph_ids)
            return [{**good, "paragraph_id": wrong.paragraph_id}]
        engine = HierarchicalRetriever(self.catalog, self.loader, malicious)
        with self.assertRaisesRegex(ValueError, "outside the selected scope or explicit details"):
            engine.search("apixaban renal dose 2.5 mg")

    def test_backend_cannot_return_stale_revision_wrong_section_or_duplicates(self):
        for changes in ({"content_hash": "old"}, {"article_id": "h"}, {"section_id": "L"},
                        {"paragraph_id": "invented"}, {"extraction_version": "old"}):
            with self.subTest(changes=changes):
                def backend(plan, article, scope, limit):
                    return [{**local_passages(plan, article, scope, limit)[0], **changes}]
                engine = HierarchicalRetriever(self.catalog, self.loader, backend)
                with self.assertRaisesRegex(ValueError, "outside the selected scope"):
                    engine.search("apixaban renal dose 2.5 mg")
        def duplicate(plan, article, scope, limit):
            hit = local_passages(plan, article, scope, limit)[0]
            return [hit, hit]
        with self.assertRaisesRegex(ValueError, "duplicate paragraph"):
            HierarchicalRetriever(self.catalog, self.loader, duplicate).search("apixaban renal dose 2.5 mg")

    def test_backend_empty_result_does_not_expand_scope(self):
        backend = Mock(return_value=[])
        result = HierarchicalRetriever(self.catalog, self.loader, backend).search("apixaban renal dose 2.5 mg")
        self.assertEqual(result["status"], "no_paragraph_match")
        backend.assert_called_once()

    def test_unresolved_subject_does_not_read_bodies(self):
        result = self.engine.search("Zzzzunknown")
        self.assertEqual(result["status"], "no_article_candidate")
        self.loader.assert_not_called()

    def test_measurement_parser_preserves_persian_digits_attached_units_and_comparators(self):
        self.assertEqual(measurements("۵mg، ۲٫۵ میلی گرم ≤۳۰ ml/min"),
                         (("5", "mg"), ("2.5", "mg"), ("<=30", "ml/min")))

    def test_route_parser_keeps_only_written_routes(self):
        self.assertEqual(route_constraints("دوز وریدی بولوس"), ("bolus", "iv"))
        self.assertEqual(route_constraints("I.V. infusion or oral"), ("infusion", "iv", "oral"))
        self.assertEqual(route_constraints("apixaban renal dose"), ())


if __name__ == "__main__":
    unittest.main()
