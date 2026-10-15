from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from apps.drugs.data.atc_reference import ATC_L2
from apps.drugs.models import AtcCategory, AtcCode, Ingredient, IngredientProfileSection

from .data.study_topics import CATEGORIES, STUDY_TOPICS
from .models import ChapterProgress, ReadDrug


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
            # All four are cardiovascular topics -> same top-level category.
            self.assertEqual(group["category_code"], "cardio-blood")
            self.assertEqual(group["category_name_fa"], "قلب، عروق و خون")

    def test_chapter_returns_drug_names_and_topics(self):
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

    def test_chapter_lists_names_only_not_lesson_text(self):
        # The list screen shows names; each drug's lesson is fetched on its
        # own when opened, so the chapter carries no lesson content at all.
        res = self.client.get("/api/v1/lessons/chapters/C07/")
        for drug in res.data["drugs"]:
            self.assertEqual(set(drug), {"slug", "name", "pharm_classes"})
        self.assertNotIn("exam_points", res.data)

    def test_lesson_drug_returns_the_lesson_text_but_not_the_raw_label(self):
        res = self.client.get(f"/api/v1/lessons/drugs/{self.metoprolol.slug}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["name"], "metoprolol")
        self.assertEqual([a["code"] for a in res.data["atc_codes"]], ["C07AB02"])

        lesson = {s["field"]: s for s in res.data["lesson_sections"]}
        self.assertEqual(lesson["contraindications"]["text_fa"], "برادی‌کاردی شدید.")
        self.assertEqual(lesson["contraindications"]["text_en"], "Severe bradycardia.")

        # `sections` is just the per-field flags: no raw label text and no
        # second copy of the summaries.
        for section in res.data["sections"]:
            self.assertEqual(set(section), {"field", "label", "has_summary"})
        self.assertTrue({s["field"]: s["has_summary"] for s in res.data["sections"]}["contraindications"])

    def test_unknown_lesson_drug_is_404(self):
        self.assertEqual(self.client.get("/api/v1/lessons/drugs/no-such-drug/").status_code, 404)

    def test_query_counts_do_not_grow_with_the_data(self):
        # The chapter list must not touch per-drug rows, and the drug lesson
        # defers raw_text -- reading it per section would add a query per row.
        for i in range(10):
            ing = _ingredient(f"betablocker{i}", f"9{i:03d}", f"C07AA{i:02d}")
            for field in ("contraindications", "warnings", "adverse_reactions"):
                IngredientProfileSection.objects.create(
                    ingredient=ing, field=field, raw_text="x", summary_fa="ف", summary_en="e",
                )
        self.client.get("/api/v1/lessons/chapters/C07/")  # warm up per-request caches
        with self.assertNumQueries(5):
            self.client.get("/api/v1/lessons/chapters/C07/")
        with self.assertNumQueries(3):
            self.client.get("/api/v1/lessons/drugs/betablocker0-9000/")

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

        self.assertTrue(
            ReadDrug.objects.filter(user=self.user, ingredient_slug=self.metoprolol.slug).exists()
        )
        # scroll_pct still lives on the per-chapter ChapterProgress row.
        progress = ChapterProgress.objects.get(user=self.user, atc_code="C07")
        self.assertEqual(progress.scroll_pct, 55)

    def test_progress_post_rejects_drug_from_another_chapter(self):
        other = _ingredient("ibuprofen", "5640", "M01AE01")
        res = self.client.post(
            "/api/v1/lessons/chapters/C07/",
            {"drug_slug": other.slug},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_reading_a_drug_marks_it_read_in_every_chapter_it_belongs_to(self):
        # A drug can legitimately carry more than one ATC code (aspirin, for
        # real: A01 dental, B01 antithrombotic, N02 analgesic) and so belongs
        # to more than one chapter. Reading it via one chapter must show it
        # already read when reached through another, unrelated chapter.
        combo = Ingredient.objects.create(name="combodrug", rxcui="424242", slug="combodrug-424242")
        c07_code, _ = AtcCode.objects.get_or_create(code="C07AA99", defaults={"name": "C07AA99"})
        n02_code, _ = AtcCode.objects.get_or_create(code="N02AA99", defaults={"name": "N02AA99"})
        combo.atc_codes.add(c07_code, n02_code)

        res = self.client.post(
            "/api/v1/lessons/chapters/C07/", {"drug_slug": combo.slug}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(combo.slug, res.data["progress"]["read_drug_slugs"])

        # Same drug, reached through the unrelated N02 chapter: already read.
        res2 = self.client.get("/api/v1/lessons/chapters/N02/")
        self.assertEqual(res2.status_code, 200)
        self.assertIn(combo.slug, res2.data["progress"]["read_drug_slugs"])

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
        # Filed under "misc" until a real topic claims it.
        self.assertEqual(fallback["category_code"], "misc")

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

    def test_category_keys_are_unique(self):
        keys = [c["key"] for c in CATEGORIES]
        self.assertEqual(len(keys), len(set(keys)))

    def test_every_topic_has_a_real_category(self):
        category_keys = {c["key"] for c in CATEGORIES}
        for topic in STUDY_TOPICS:
            with self.subTest(topic=topic["key"]):
                self.assertIn(topic.get("category"), category_keys)

    def test_every_category_has_at_least_one_topic(self):
        used = {topic["category"] for topic in STUDY_TOPICS}
        orphans = {c["key"] for c in CATEGORIES} - used
        self.assertEqual(orphans, set(), f"Unused categories: {sorted(orphans)}")


class DrugSearchTests(TestCase):
    """GET /lessons/search/?q= -- quick find by English or Persian name."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="s", email="s@example.com", password="x")
        self.client.force_authenticate(self.user)
        c = AtcCategory.objects.create(code="C", name_en="Cardiovascular system", name_fa="قلب و عروق", level=1)
        b = AtcCategory.objects.create(code="B", name_en="Blood", name_fa="خون", level=1)
        n = AtcCategory.objects.create(code="N", name_en="Nervous system", name_fa="عصبی", level=1)
        AtcCategory.objects.create(code="C07", name_en="Beta blocking agents", name_fa="مسدودکننده‌های بتا", level=2, parent=c)
        AtcCategory.objects.create(code="B01", name_en="Antithrombotic agents", name_fa="ضدترومبوز", level=2, parent=b)
        AtcCategory.objects.create(code="N02", name_en="Analgesics", name_fa="مسکن‌ها", level=2, parent=n)

        self.metoprolol = _ingredient("metoprolol", "6918", "C07AB02")
        self.metoprolol.name_fa = "متوپرولول"
        self.metoprolol.save()
        aspirin = _ingredient("aspirin", "1191", "N02BA01")
        aspirin.atc_codes.add(AtcCode.objects.create(code="B01AC06", name="aspirin"))
        aspirin.name_fa = "آسپرین"
        aspirin.save()
        ceftobiprole = _ingredient("ceftobiprole", "1000", "C07ZZ99")
        ceftobiprole.name_fa = "سفتوبی‌پرول"
        ceftobiprole.save()
        # no ATC code -> in no lesson chapter -> never a result
        Ingredient.objects.create(name="metoclopramide-x", name_fa="متوکلوپرامید", rxcui="9", slug="mx-9")

    def search(self, q):
        res = self.client.get("/api/v1/lessons/search/", {"q": q})
        self.assertEqual(res.status_code, 200)
        return res.data

    def test_english_and_persian_names(self):
        self.assertEqual([r["slug"] for r in self.search("metop")], [self.metoprolol.slug])
        result = self.search("متوپرو")[0]
        self.assertEqual((result["name"], result["name_fa"]), ("metoprolol", "متوپرولول"))
        self.assertEqual(result["chapters"], [{"code": "C07", "name_fa": "مسدودکننده‌های بتا", "name_en": "Beta blocking agents"}])

    def test_persian_spellings_fold_together(self):
        for q in ["سفتوبی پرول", "سفتوبیپرول", "سفتوبيپرول", "سفتوبی‌پرول"]:
            self.assertEqual([r["name"] for r in self.search(q)], ["ceftobiprole"], q)
        self.assertEqual([r["name"] for r in self.search("اسپرین")], ["aspirin"])  # آ typed as ا

    def test_every_chapter_of_a_drug_is_listed(self):
        chapters = self.search("aspirin")[0]["chapters"]
        self.assertEqual([c["code"] for c in chapters], ["B01", "N02"])

    def test_better_matches_first(self):
        _ingredient("pro", "2000", "C07AA01")
        names = [r["name"] for r in self.search("pro")]
        self.assertEqual(names[0], "pro")  # exact before partial
        self.assertIn("metoprolol", names)

    def test_drugs_outside_the_lessons_are_left_out(self):
        self.assertEqual(self.search("متوکلو"), [])

    def test_too_short_or_empty(self):
        self.assertEqual(self.search("m"), [])
        self.assertEqual(self.search(""), [])

    def test_needs_sign_in(self):
        self.assertEqual(APIClient().get("/api/v1/lessons/search/", {"q": "metop"}).status_code, 401)
