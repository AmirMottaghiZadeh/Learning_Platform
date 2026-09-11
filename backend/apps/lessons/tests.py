from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from apps.drugs.data.atc_reference import ATC_L2
from apps.drugs.models import AtcCategory, AtcCode, Ingredient, IngredientProfileSection

from .data.study_topics import STUDY_TOPICS
from .models import ChapterProgress


def _ingredient(name, rxcui, atc_code):
    ing = Ingredient.objects.create(name=name, rxcui=rxcui, slug=f"{name}-{rxcui}")
    code, _ = AtcCode.objects.get_or_create(code=atc_code, defaults={"name": atc_code})
    ing.atc_codes.add(code)
    return ing


class LessonTaxonomyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="learner", email="l@example.com", password="x"
        )
        self.client.force_authenticate(self.user)

        c = AtcCategory.objects.create(code="C", name_en="Cardiovascular system",
                                       name_fa="قلب و عروق", level=1)
        AtcCategory.objects.create(code="C07", name_en="Beta blocking agents",
                                   name_fa="مسدودکننده‌های بتا", level=2, parent=c)
        AtcCategory.objects.create(code="C03", name_en="Diuretics",
                                   name_fa="دیورتیک‌ها", level=2, parent=c)
        # C07 has two drugs; C03 has none -> C03 must not appear; empty L1s hidden
        n = AtcCategory.objects.create(code="N", name_en="Nervous system",
                                       name_fa="عصبی", level=1)
        AtcCategory.objects.create(code="N02", name_en="Analgesics",
                                   name_fa="مسکن‌ها", level=2, parent=n)

        self.metoprolol = _ingredient("metoprolol", "6918", "C07AB02")
        _ingredient("atenolol", "1202", "C07AB03")
        IngredientProfileSection.objects.create(
            ingredient=self.metoprolol, field="contraindications",
            raw_text="Severe bradycardia.", summary_fa="برادی‌کاردی شدید.",
            summary_en="Severe bradycardia.",
        )
        IngredientProfileSection.objects.create(
            ingredient=self.metoprolol, field="clinical_pharmacology",
            raw_text="Beta-1 blockade.", summary_fa="مهار بتا-۱.", summary_en="Beta-1 blockade.",
        )

    def test_groups_lists_only_populated_subgroups(self):
        res = self.client.get("/api/v1/lessons/groups/")
        self.assertEqual(res.status_code, 200)

        # C07 (beta blockers) is curated under four clinical topics (it is
        # first-line for hypertension, heart failure, angina AND arrhythmia);
        # every one of them must appear, each holding just the C07 chapter.
        # C03 (no drugs in this fixture) and N02 (no drugs) must not appear
        # anywhere, including inside those same topics (cv-htn/cv-hf also
        # list C03).
        codes = {g["code"] for g in res.data}
        self.assertEqual(codes, {"cv-htn", "cv-hf", "cv-angina", "cv-arrhythmia"})

        for group in res.data:
            sub_codes = {s["code"] for s in group["subgroups"]}
            self.assertEqual(sub_codes, {"C07"})
            c07 = group["subgroups"][0]
            self.assertEqual(c07["total"], 2)
            self.assertEqual(c07["done"], 0)

    def test_chapter_returns_drugs_exam_points_and_topics(self):
        res = self.client.get("/api/v1/lessons/chapters/c07/")  # case-insensitive
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["name_fa"], "مسدودکننده‌های بتا")
        self.assertEqual({d["name"] for d in res.data["drugs"]}, {"metoprolol", "atenolol"})

        # Primary topic = the first one listing C07 in STUDY_TOPICS order.
        self.assertEqual(res.data["group_code"], "cv-htn")
        self.assertEqual(res.data["group_name_fa"], "فشار خون بالا")
        topic_codes = {t["code"] for t in res.data["topics"]}
        self.assertEqual(topic_codes, {"cv-htn", "cv-hf", "cv-angina", "cv-arrhythmia"})

        # The real ATC anatomical group survives, unmodified, for rigour.
        self.assertEqual(res.data["anatomical_name_fa"], "قلب و عروق")

        points = res.data["exam_points"]
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0]["field"], "contraindications")
        self.assertEqual(points[0]["tone"], "deny")
        self.assertEqual(points[0]["drug_name"], "metoprolol")

    def test_unknown_chapter_is_404(self):
        self.assertEqual(self.client.get("/api/v1/lessons/chapters/C03/").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/lessons/chapters/ZZ9/").status_code, 404)

    def test_progress_post_marks_read_and_updates_done_count(self):
        res = self.client.post(
            "/api/v1/lessons/chapters/C07/",
            {"drug_slug": self.metoprolol.slug, "scroll_pct": 55},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["progress"]["read_drug_slugs"], [self.metoprolol.slug])
        self.assertEqual(res.data["progress"]["scroll_pct"], 55)

        groups = self.client.get("/api/v1/lessons/groups/").data
        c07 = groups[0]["subgroups"][0]
        self.assertEqual(c07["done"], 1)

        progress = ChapterProgress.objects.get(user=self.user, atc_code="C07")
        self.assertEqual(progress.read_drug_slugs, [self.metoprolol.slug])

    def test_progress_post_rejects_drug_from_another_chapter(self):
        other = _ingredient("ibuprofen", "5640", "M01AE01")
        res = self.client.post(
            "/api/v1/lessons/chapters/C07/",
            {"drug_slug": other.slug},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_requires_authentication(self):
        self.assertEqual(APIClient().get("/api/v1/lessons/groups/").status_code, 401)


class LessonTaxonomyFallbackTests(TestCase):
    """A populated L2 code the curated topics don't cover (e.g. a brand-new
    ATC class, added to the reference before someone decides where it belongs
    in study_topics.py) must still show up — grouped by its ATC anatomical
    section — instead of silently vanishing from the lessons list."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="learner2", email="l2@example.com", password="x"
        )
        self.client.force_authenticate(self.user)
        z = AtcCategory.objects.create(code="Z", name_en="Made-up section",
                                        name_fa="بخش ساختگی", level=1)
        AtcCategory.objects.create(code="Z99", name_en="Made-up class",
                                    name_fa="دستهٔ ساختگی", level=2, parent=z)
        _ingredient("newdrug", "999999", "Z99AA01")

    def test_uncovered_code_falls_back_to_atc_l1(self):
        res = self.client.get("/api/v1/lessons/groups/")
        self.assertEqual(res.status_code, 200)
        fallback = next(g for g in res.data if g["code"] == "other-Z")
        self.assertEqual(fallback["name_fa"], "بخش ساختگی")
        self.assertEqual({s["code"] for s in fallback["subgroups"]}, {"Z99"})

    def test_uncovered_chapter_topic_falls_back_to_atc_l1(self):
        res = self.client.get("/api/v1/lessons/chapters/Z99/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["group_code"], "other-Z")
        self.assertEqual(res.data["group_name_fa"], "بخش ساختگی")
        self.assertEqual([t["code"] for t in res.data["topics"]], ["other-Z"])


class StudyTopicsCoverageTests(SimpleTestCase):
    """Static checks on the curated table itself — no DB needed. Keeps
    `study_topics.py` internally consistent and catches a newly-imported ATC
    class that nobody has assigned a study topic to yet."""

    def test_every_bundled_l2_code_is_covered(self):
        covered = {code for topic in STUDY_TOPICS for code in topic["l2"]}
        missing = set(ATC_L2) - covered
        self.assertEqual(
            missing, set(),
            f"These ATC L2 codes have no study topic yet: {sorted(missing)}. "
            "Add them to apps/lessons/data/study_topics.py.",
        )

    def test_no_unknown_l2_codes(self):
        covered = {code for topic in STUDY_TOPICS for code in topic["l2"]}
        unknown = covered - set(ATC_L2)
        self.assertEqual(
            unknown, set(),
            f"study_topics.py references L2 codes not in ATC_L2 (typo?): {sorted(unknown)}",
        )

    def test_topic_keys_are_unique(self):
        keys = [topic["key"] for topic in STUDY_TOPICS]
        self.assertEqual(len(keys), len(set(keys)))

    def test_no_duplicate_l2_within_a_topic(self):
        for topic in STUDY_TOPICS:
            with self.subTest(topic=topic["key"]):
                self.assertEqual(len(topic["l2"]), len(set(topic["l2"])))
