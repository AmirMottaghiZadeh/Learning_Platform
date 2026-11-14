import uuid
from django.test import TestCase,SimpleTestCase
from . import media
from .models import RetrievalGeneration,ReferenceMedia


class MediaIntentTests(SimpleTestCase):
    def test_media_intent_does_not_treat_dosage_form_as_a_figure(self):
        self.assertFalse(media.requested("شکل دارویی این دارو چیست؟"))
        for query in ["جدول درمان کودکان","عکس بیماری","شکل شماره ۲","show the management table"]:
            self.assertTrue(media.requested(query))


class MediaSearchTests(TestCase):
    databases={"default","reference_search"}

    def setUp(self):
        self.generation=RetrievalGeneration.objects.create(source_identity="a"*64,source_revision="r",source_generation=uuid.uuid4(),
            source_version="fixture",chunker_version="fixture",expected_articles=1,status="ready")
        ReferenceMedia.objects.create(generation=self.generation,source_id="1",content_hash="b"*64,media_key="um-"+"c"*32,
            kind="table",article_title="Nocturnal enuresis in children",title="Initial management",caption="Original table",
            search_text="Nocturnal enuresis children initial management table treatment",evidence_text="Original source table",
            audience="pediatric",descriptor={"content_complete":True})

    def test_caption_search_returns_a_media_citation_with_the_original_article(self):
        rows=media.search(self.generation,"show nocturnal enuresis table",audience="pediatric")
        self.assertEqual(len(rows),1);self.assertEqual(rows[0].article_id,"1")
        self.assertEqual(rows[0].media[0]["kind"],"table")
        self.assertEqual(rows[0].target["params"]["mediaContentHash"],"b"*64)

    def test_generation_and_population_are_respected(self):
        self.assertEqual(media.search(self.generation,"nocturnal enuresis",audience="adult"),[])
        other=RetrievalGeneration.objects.create(source_identity="d"*64,source_revision="r",source_generation=uuid.uuid4(),
            source_version="fixture",chunker_version="fixture",expected_articles=1,status="ready")
        self.assertEqual(media.search(other,"nocturnal enuresis",audience="pediatric"),[])

    def test_requested_kind_and_primary_topic_exclude_incidental_mentions(self):
        original=ReferenceMedia.objects.get(generation=self.generation)
        ReferenceMedia.objects.create(generation=self.generation,source_id="2",content_hash="d"*64,
            media_key="um-"+"d"*32,kind="table",article_title="Obesity in children",title="Comorbidities",
            caption="Obesity complications",search_text="Obesity children nocturnal enuresis table management treatment",
            evidence_text="Incidental enuresis mention",audience="pediatric")
        original.pk=None;original.media_key="um-"+"e"*32;original.kind="image";original.save()
        rows=media.search(self.generation,"nocturnal enuresis children initial management table",audience="pediatric")
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0].media[0]["kind"],"table")
        rows=media.search(self.generation,"nocturnal enuresis image",audience="pediatric")
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0].media[0]["kind"],"image")
