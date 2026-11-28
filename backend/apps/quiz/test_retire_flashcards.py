from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient


class FlashcardRemovalMigrationTests(TransactionTestCase):
    """Exercise the actual upgrade against seeded historical user records."""

    def test_removal_preserves_questions_and_shared_facts(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        old = [
            ("flashcards", "0006_leitner_by_section"),
            ("quiz", "0009_alter_quizquestion_prompts"),
            ("progress", "0003_plan_start_and_rollover"),
            ("billing", "0011_order_channel"),
            ("activity", "0002_activityevent_area_activityevent_viewport_and_more"),
            ("announcements", "0002_alter_appannouncement_audience_and_more"),
        ]
        try:
            executor.migrate(old)
            apps = executor.loader.project_state(old).apps
            user = apps.get_model(settings.AUTH_USER_MODEL).objects.create(username="retirement-test")
            ingredient = apps.get_model("drugs", "Ingredient").objects.create(
                rxcui="retirement-test", slug="retirement-test", name="Example"
            )
            apps.get_model("flashcards", "LeitnerCard").objects.create(user=user, ingredient=ingredient, section="indication")
            apps.get_model("flashcards", "TopicProgress").objects.create(user=user, topic_key="cv-htn", position=1)
            fact = apps.get_model("flashcards", "FlashcardFact").objects.create(
                ingredient=ingredient, section="indication", lang="fa", order=0, text="Preserved shared fact"
            )
            session = apps.get_model("quiz", "QuizSession").objects.create(user=user, category="cv-htn", question_count=5)
            bank = apps.get_model("quiz", "BankQuestion").objects.create(
                ingredient=ingredient, field="indication", prompt_fa="Preserved question", options_fa=["A", "B", "C", "D"], correct_index=0
            )
            question = apps.get_model("quiz", "QuizQuestion").objects.create(
                session=session, order=1, prompt_fa="Preserved question", prompt_en="Preserved question",
                options_fa=["A", "B", "C", "D"], correct_index=0, bank_question=bank
            )
            answer = apps.get_model("quiz", "QuizAnswer").objects.create(question=question, selected_index=1, is_correct=False)
            plan = apps.get_model("progress", "StudyPlan").objects.create(user=user)
            items = apps.get_model("progress", "StudyPlanItem")
            for activity in ["flashcards", "quiz"]:
                items.objects.create(plan=plan, day=timezone.localdate(), activity_type=activity)
            billing_plan = apps.get_model("billing", "Plan").objects.create(slug="preserved-plan", name_fa="Example")
            entitlement = apps.get_model("billing", "Entitlement").objects.create(
                user=user, plan=billing_plan, source="admin", features={"flashcards": {}, "quiz": {"limit": None}}
            )
            events = apps.get_model("activity", "ActivityEvent")
            for section in ["flashcards", "quiz"]:
                events.objects.create(user=user, source="app", section=section, action="view")
            announcement = apps.get_model("announcements", "AppAnnouncement").objects.create(
                title="Old link", body="Example", link_screen="leitner"
            )

            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            apps = executor.loader.project_state(latest).apps
            self.assertEqual(apps.get_model("quiz", "StudyFact").objects.get(pk=fact.pk).text, "Preserved shared fact")
            self.assertTrue(apps.get_model("quiz", "QuizSession").objects.filter(pk=session.pk).exists())
            self.assertTrue(apps.get_model("quiz", "BankQuestion").objects.filter(pk=bank.pk).exists())
            self.assertTrue(apps.get_model("quiz", "QuizAnswer").objects.filter(pk=answer.pk, is_correct=False).exists())
            self.assertNotIn("flashcards_leitnercard", connection.introspection.table_names())
            self.assertNotIn("flashcards_topicprogress", connection.introspection.table_names())
            self.assertEqual(list(apps.get_model("progress", "StudyPlanItem").objects.filter(plan_id=plan.pk).values_list("activity_type", flat=True)), ["quiz"])
            self.assertEqual(apps.get_model("billing", "Entitlement").objects.get(pk=entitlement.pk).features, {"quiz": {"limit": None}})
            self.assertFalse(apps.get_model("billing", "Feature").objects.filter(key="flashcards").exists())
            self.assertEqual(list(apps.get_model("activity", "ActivityEvent").objects.filter(user_id=user.pk).values_list("section", flat=True)), ["quiz"])
            self.assertEqual(apps.get_model("announcements", "AppAnnouncement").objects.get(pk=announcement.pk).link_screen, "lessons")
        finally:
            MigrationExecutor(connection).migrate(latest)


class RemovedFlashcardEndpointTests(TransactionTestCase):
    @override_settings(FLASHCARDS_API_ENABLED=True)
    def test_retired_endpoints_cannot_be_reenabled(self):
        for prefix in ["/api/v1/", "/api/"]:
            for path in ["flashcards/", "flashcards/decks/", "flashcards/leitner/"]:
                self.assertEqual(APIClient().get(prefix + path).status_code, 404)
