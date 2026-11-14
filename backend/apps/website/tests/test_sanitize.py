from django.test import SimpleTestCase

from apps.website.sanitize import clean_html, plain_text, safe_url


class SanitizeTests(SimpleTestCase):
    def test_keeps_basic_formatting(self):
        html = '<h2>عنوان</h2><p>متن <strong>پررنگ</strong> و <em>کج</em></p><ul><li>یک</li></ul>'
        self.assertEqual(clean_html(html), html)

    def test_drops_script_with_content(self):
        self.assertEqual(clean_html('<p>a</p><script>alert(1)</script><p>b</p>'), "<p>a</p><p>b</p>")

    def test_drops_event_handlers_and_style(self):
        out = clean_html('<p onclick="x()" style="color:red">hi</p><img src="/a.png" onerror="x()" alt="t">')
        self.assertNotIn("onclick", out)
        self.assertNotIn("style", out)
        self.assertNotIn("onerror", out)
        self.assertIn('<img src="/a.png" alt="t">', out)

    def test_javascript_urls_removed(self):
        out = clean_html('<a href="javascript:alert(1)">x</a><a href="  JaVaScRiPt:alert(1)">y</a><a href="data:text/html,x">z</a>')
        self.assertNotIn("javascript", out.lower())
        self.assertNotIn("data:", out)

    def test_allows_http_mailto_and_relative_links(self):
        out = clean_html('<a href="https://x.ir/a?b=1&c=2">a</a><a href="mailto:a@b.ir">b</a><a href="/blog/">c</a><a href="#x">d</a>')
        self.assertIn('href="https://x.ir/a?b=1&amp;c=2"', out)
        self.assertIn('href="mailto:a@b.ir"', out)
        self.assertIn('href="/blog/"', out)
        self.assertIn('href="#x"', out)

    def test_protocol_relative_url_refused(self):
        self.assertEqual(safe_url("//evil.com/x"), "")

    def test_external_links_get_rel(self):
        self.assertIn('rel="noopener noreferrer"', clean_html('<a href="https://x.ir" target="_blank">x</a>'))

    def test_iframe_object_form_dropped(self):
        out = clean_html('<iframe src="https://x"></iframe><object data="x"></object><form action="/x"><input name="a"></form><p>ok</p>')
        self.assertEqual(out, "<p>ok</p>")

    def test_unknown_tags_unwrapped_and_balanced(self):
        self.assertEqual(clean_html("<custom>text</custom><p>open"), "text<p>open</p>")

    def test_only_listed_classes(self):
        out = clean_html('<div class="callout evil">x</div>')
        self.assertEqual(out, '<div class="callout">x</div>')

    def test_text_is_escaped(self):
        self.assertEqual(clean_html("<p>1 < 2 & 3</p>"), "<p>1 &lt; 2 &amp; 3</p>")

    def test_self_closing_script_does_not_swallow_rest(self):
        self.assertEqual(clean_html("<script/><p>kept</p>"), "<p>kept</p>")

    def test_plain_text(self):
        self.assertEqual(plain_text("<h2>یک</h2><p>دو  <b>سه</b></p><script>x</script>"), "یک دو سه")
