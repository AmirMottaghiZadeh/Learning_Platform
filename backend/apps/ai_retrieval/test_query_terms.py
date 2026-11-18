from django.test import SimpleTestCase
from .query_terms import question_key, query_text, unique_words
from .scope import SourceScope


class QueryNormalizationTests(SimpleTestCase):
    def test_unicode_search_normalization_is_local_and_preserves_medical_digits(self):
        self.assertEqual(query_text("  ARIPIPRAZOLE—monitoring "),"aripiprazole monitoring")
        self.assertEqual(query_text("كودك ۱۲ ساله"),"کودک 12 ساله")
        self.assertEqual(unique_words("dose dose adverse effects"),["dose","adverse","effects"])

    def test_plan_identity_preserves_decimals_negation_and_signs(self):
        self.assertNotEqual(question_key("eGFR=2.5"),question_key("eGFR=25"))
        self.assertNotEqual(question_key("does not breathe"),question_key("does breathe"))

    def test_roots_cannot_be_rebound_and_links_require_a_known_parent(self):
        scope=SourceScope();scope.bind(["10"])
        self.assertFalse(scope.follow("unknown","20",limit=2))
        self.assertTrue(scope.follow("10","20",limit=2))
        self.assertTrue(scope.follow("20","30",limit=2))
        self.assertFalse(scope.follow("30","40",limit=2))
        with self.assertRaises(ValueError):scope.bind(["99"])
