from html.parser import HTMLParser
import unittest

from apps.uptodate.search_extraction import ANCHOR_ATTRIBUTE, extract_article


class _Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if ANCHOR_ATTRIBUTE in values:
            self.values.append(values[ANCHOR_ATTRIBUTE])


class ExtractionTests(unittest.TestCase):
    def test_inline_heading_prose_is_searchable_and_title_stays_short(self):
        html = ('<div id="topicText"><p class="headingAnchor" id="H1">'
                '<span class="h2">Kidney <b>impairment</b></span>'
                '<span class="headingEndMark"> — </span>'
                'Keep this clinical instruction, including <a href="#ref">its reference</a>.</p>'
                '<p>Next instruction.</p></div>')
        article = extract_article("1", html)
        self.assertEqual(len(article.blocks), 2)
        self.assertEqual(article.blocks[0].text,
                         "Kidney impairment — Keep this clinical instruction, including its reference.")
        self.assertTrue(all(b.section_title == "Kidney impairment" for b in article.blocks))
        self.assertTrue(all(b.section_id == "H1" for b in article.blocks))
        parser = _Anchors()
        parser.feed(article.html)
        self.assertEqual(parser.values, [b.paragraph_id for b in article.blocks])
        self.assertIn('class="headingAnchor" id="H1"', article.html)

    def test_heading_without_following_prose_does_not_create_an_empty_passage(self):
        article = extract_article("1", '<p class="headingAnchor" id="H1">'
                                  '<span class="h3">Treatment</span><span> — </span></p><p>Body.</p>')
        self.assertEqual([b.text for b in article.blocks], ["Body."])
        self.assertEqual(article.blocks[0].section_title, "Treatment")

    def test_blocks_are_annotated_and_references_excluded(self):
        html = ('<div id="topicText"><p id="H1" class="headingAnchor">Treatment</p>'
                '<p>A <b>dose</b> of 5 mg.</p><ul><li>One <ul><li>Two</li></ul></li></ul>'
                '<table><tr><th>Drug</th><td>5 mg</td></tr></table>'
                '<div id="references"><ol><li>Reference only</li></ol></div></div>')
        result = extract_article("123", html)
        self.assertEqual([b.kind for b in result.blocks], ["p", "li", "tr"])
        self.assertEqual([b.text for b in result.blocks], ["A dose of 5 mg.", "One Two", "Drug 5 mg"])
        self.assertTrue(all(b.section_id == "H1" and b.section_title == "Treatment" for b in result.blocks))
        parser = _Anchors()
        parser.feed(result.html)
        self.assertEqual(parser.values, [b.paragraph_id for b in result.blocks])
        self.assertEqual(len(set(parser.values)), len(parser.values))

    def test_anchor_is_stable_for_same_article_and_changes_with_revision(self):
        html = '<p class="headingAnchor" id="H1">Title</p><p>Text.</p>'
        original = extract_article("7", html)
        self.assertEqual(original, extract_article("7", html))
        self.assertNotEqual(original.blocks[0].paragraph_id, extract_article("8", html).blocks[0].paragraph_id)
        self.assertNotEqual(original.blocks[0].paragraph_id, extract_article("7", html + " ").blocks[0].paragraph_id)
        self.assertNotEqual(original.content_hash, extract_article("7", html + " ").content_hash)

    def test_scripts_and_reserved_attribute_are_not_processed_as_content(self):
        result = extract_article("1", '<script>secret</script><p>Visible<br>text</p>')
        self.assertEqual([b.text for b in result.blocks], ["Visible text"])
        with self.assertRaises(ValueError):
            extract_article("1", f'<p {ANCHOR_ATTRIBUTE}="pretend">Text</p>')

    def test_nested_excluded_markup_does_not_close_parent_block(self):
        article = extract_article("1", '<p>Before <span id="references"><p>Hidden</p></span> after.</p>')
        self.assertEqual([b.text for b in article.blocks], ["Before after."])

    def test_drug_monograph_sections_use_nearest_container(self):
        html = ('<div id="F123"><h2>Dosage</h2><p>First section</p></div>'
                '<div id="F456"><h2>Warnings</h2><p>Second section</p></div>')
        blocks = extract_article("1", html).blocks
        self.assertEqual([(b.section_id, b.section_title) for b in blocks],
                         [("F123", "Dosage"), ("F456", "Warnings")])

    def test_body_scope_and_table_headers(self):
        html = ('<div><p>Header outside</p><div id="topicText">'
                '<p class="headingAnchor" id="H1">Dose</p><table>'
                '<tr><th>Drug</th><th>Dose</th></tr><tr><td>A</td><td>5 mg</td></tr>'
                '</table></div><p>Footer outside</p></div>')
        result = extract_article("1", html)
        self.assertEqual([b.text for b in result.blocks], ["Drug Dose", "A 5 mg"])
        self.assertEqual(result.blocks[1].table_headers, ("Drug", "Dose"))
        with self.assertRaises(ValueError):
            extract_article("1", '<div id="topicText"></div><div id="topicText"></div>')
        with self.assertRaises(ValueError):
            extract_article("1", '<p>Only a fragment</p>', require_topic=True)

    def test_complex_tables_do_not_emit_misleading_header_context(self):
        html = ('<div id="topicText"><table><tr><th colspan="2">Group</th></tr>'
                '<tr><th>Drug</th><th>Dose</th></tr><tr><td>A</td><td>5 mg</td></tr></table>'
                '<table><tr><th>Name</th><th>Value</th></tr><tr><td>B</td><td>7</td></tr></table></div>')
        blocks = extract_article("1", html, require_topic=True).blocks
        self.assertEqual([b.table_context_status for b in blocks],
                         ["complex_review"] * 3 + ["simple"] * 2)
        self.assertTrue(all(not b.table_headers for b in blocks[:3]))
        self.assertEqual(blocks[-1].table_headers, ("Name", "Value"))

    def test_nested_table_and_multiple_header_rows_are_flagged(self):
        html = ('<table><tr><th>A</th></tr><tr><th>B</th></tr><tr><td>1</td></tr></table>'
                '<table><tr><td><table><tr><td>Nested</td></tr></table></td></tr></table>')
        blocks = extract_article("1", html).blocks
        self.assertTrue(all(b.table_context_status == "complex_review" for b in blocks))
        self.assertTrue(all(not b.table_headers for b in blocks))


if __name__ == "__main__":
    unittest.main()
