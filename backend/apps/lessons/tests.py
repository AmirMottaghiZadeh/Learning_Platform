from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.drugs.models import AtcCategory, AtcCode, Ingredient, IngredientProfileSection

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

        codes = {g["code"] for g in res.data}
        self.assertEqual(codes, {"C"})  # N has no drugs -> hidden

        cardio = next(g for g in res.data if g["code"] == "C")
        sub_codes = {s["code"] for s in cardio["subgroups"]}
        self.assertEqual(sub_codes, {"C07"})  # C03 empty -> hidden
        c07 = cardio["subgroups"][0]
        self.assertEqual(c07["total"], 2)
        self.assertEqual(c07["done"], 0)

    def test_chapter_returns_drugs_exam_points_and_group_name(self):
        res = self.client.get("/api/v1/lessons/chapters/c07/")  # case-insensitive
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["name_fa"], "مسدودکننده‌های بتا")
        self.assertEqual(res.data["group_name_fa"], "قلب و عروق")
        self.assertEqual({d["name"] for d in res.data["drugs"]}, {"metoprolol", "atenolol"})

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
