from django.db import migrations
from django.db.models import Q


LEGACY_PRODUCT_IDS = ("k_game", "k-game")
PRODUCT_ID = "pharmexa"
LEGACY_REVIEW_RULE_VERSIONS = ("k-game-leitner-box-v1",)
REVIEW_RULE_VERSION = "pharmexa-leitner-box-v1"


def merge_flashcard_states(apps, old_source, new_source):
    FlashcardReview = apps.get_model("flashcards", "FlashcardReview")
    FlashcardState = apps.get_model("flashcards", "FlashcardState")

    for old_state in FlashcardState.objects.filter(knowledge_source=old_source):
        new_state = FlashcardState.objects.filter(
            user_id=old_state.user_id,
            knowledge_source=new_source,
        ).first()
        if new_state is None:
            old_state.knowledge_source = new_source
            old_state.save(update_fields=["knowledge_source"])
            continue

        FlashcardReview.objects.filter(state=old_state).update(state=new_state)
        new_state.review_count += old_state.review_count
        new_state.lapse_count += old_state.lapse_count
        if (
            old_state.last_reviewed_at
            and (
                new_state.last_reviewed_at is None
                or old_state.last_reviewed_at > new_state.last_reviewed_at
            )
        ):
            new_state.box = old_state.box
            new_state.review_state = old_state.review_state
            new_state.interval_days = old_state.interval_days
            new_state.last_rating = old_state.last_rating
            new_state.schedule_rule_version = old_state.schedule_rule_version
            new_state.due_at = old_state.due_at
            new_state.last_reviewed_at = old_state.last_reviewed_at
        new_state.save(
            update_fields=[
                "box",
                "review_state",
                "interval_days",
                "review_count",
                "lapse_count",
                "last_rating",
                "schedule_rule_version",
                "due_at",
                "last_reviewed_at",
            ]
        )
        old_state.delete()


def merge_mistakes(apps, old_source, new_source):
    Mistake = apps.get_model("games", "Mistake")

    for old_mistake in Mistake.objects.filter(knowledge_source=old_source):
        new_mistake = Mistake.objects.filter(
            user_id=old_mistake.user_id,
            topic_key=old_mistake.topic_key,
            knowledge_source=new_source,
        ).first()
        if new_mistake is None:
            old_mistake.knowledge_source = new_source
            old_mistake.save(update_fields=["knowledge_source"])
            continue

        new_mistake.wrong_count += old_mistake.wrong_count
        if old_mistake.last_at > new_mistake.last_at:
            new_mistake.last_wrong_answer = old_mistake.last_wrong_answer
            new_mistake.last_at = old_mistake.last_at
        new_mistake.save(update_fields=["wrong_count", "last_wrong_answer", "last_at"])
        old_mistake.delete()


def merge_knowledge_sources(apps):
    GameQuestion = apps.get_model("games", "GameQuestion")
    KnowledgeSource = apps.get_model("learning", "KnowledgeSource")

    for old_source in KnowledgeSource.objects.filter(product_id__in=LEGACY_PRODUCT_IDS):
        new_source = KnowledgeSource.objects.filter(
            product_id=PRODUCT_ID,
            external_id=old_source.external_id,
        ).first()
        if new_source is None:
            old_source.product_id = PRODUCT_ID
            old_source.save(update_fields=["product_id"])
            continue

        GameQuestion.objects.filter(knowledge_source=old_source).update(
            knowledge_source=new_source
        )
        merge_mistakes(apps, old_source, new_source)
        merge_flashcard_states(apps, old_source, new_source)
        old_source.delete()


def merge_learning_objects(apps):
    KnowledgeSource = apps.get_model("learning", "KnowledgeSource")
    LearningObject = apps.get_model("learning", "LearningObject")

    for old_object in LearningObject.objects.filter(product_id__in=LEGACY_PRODUCT_IDS):
        new_object = LearningObject.objects.filter(
            product_id=PRODUCT_ID,
            external_id=old_object.external_id,
        ).first()
        if new_object is None:
            old_object.product_id = PRODUCT_ID
            old_object.save(update_fields=["product_id"])
            continue

        KnowledgeSource.objects.filter(learning_object=old_object).update(
            learning_object=new_object
        )
        old_object.delete()


def merge_progress(apps, old_topic, new_topic):
    LearnerProgress = apps.get_model("learning", "LearnerProgress")

    for old_progress in LearnerProgress.objects.filter(
        Q(topic=old_topic) | Q(product_id__in=LEGACY_PRODUCT_IDS, topic=new_topic)
    ):
        new_progress = LearnerProgress.objects.filter(
            learner_id=old_progress.learner_id,
            product_id=PRODUCT_ID,
            topic=new_topic,
        ).exclude(id=old_progress.id).first()
        if new_progress is None:
            old_progress.product_id = PRODUCT_ID
            old_progress.topic = new_topic
            old_progress.save(update_fields=["product_id", "topic"])
            continue

        for field in (
            "questions_answered",
            "correct_answers",
            "wrong_answers",
            "timed_out_answers",
            "xp",
            "review_count",
            "mistake_count",
        ):
            setattr(new_progress, field, getattr(new_progress, field) + getattr(old_progress, field))
        if (
            old_progress.last_activity_at
            and (
                new_progress.last_activity_at is None
                or old_progress.last_activity_at > new_progress.last_activity_at
            )
        ):
            new_progress.last_activity_at = old_progress.last_activity_at
            new_progress.mastery_state = old_progress.mastery_state
        new_progress.save(
            update_fields=[
                "questions_answered",
                "correct_answers",
                "wrong_answers",
                "timed_out_answers",
                "xp",
                "review_count",
                "mistake_count",
                "last_activity_at",
                "mastery_state",
            ]
        )
        old_progress.delete()


def merge_topics(apps):
    KnowledgeSource = apps.get_model("learning", "KnowledgeSource")
    LearningObject = apps.get_model("learning", "LearningObject")
    LearningTopic = apps.get_model("learning", "LearningTopic")

    for old_topic in LearningTopic.objects.filter(product_id__in=LEGACY_PRODUCT_IDS):
        new_topic = LearningTopic.objects.filter(
            product_id=PRODUCT_ID,
            key=old_topic.key,
        ).first()
        if new_topic is None:
            old_topic.product_id = PRODUCT_ID
            old_topic.save(update_fields=["product_id"])
            new_topic = old_topic

        merge_progress(apps, old_topic, new_topic)
        if old_topic.id == new_topic.id:
            continue
        LearningObject.objects.filter(topic=old_topic).update(topic=new_topic)
        KnowledgeSource.objects.filter(topic=old_topic).update(topic=new_topic)
        old_topic.delete()


def merge_league_data(apps):
    LeagueResult = apps.get_model("league", "LeagueResult")
    LeagueSeason = apps.get_model("league", "LeagueSeason")

    for old_season in LeagueSeason.objects.filter(product_id__in=LEGACY_PRODUCT_IDS):
        new_season = LeagueSeason.objects.filter(
            product_id=PRODUCT_ID,
            key=old_season.key,
        ).first()
        if new_season is None:
            old_season.product_id = PRODUCT_ID
            old_season.save(update_fields=["product_id"])
            new_season = old_season
        LeagueResult.objects.filter(season=old_season).update(
            season=new_season,
            product_id=PRODUCT_ID,
        )
        if old_season.id != new_season.id:
            old_season.delete()

    LeagueResult.objects.filter(product_id__in=LEGACY_PRODUCT_IDS).update(
        product_id=PRODUCT_ID
    )


def rename_legacy_product(apps, schema_editor):
    LearningEventRecord = apps.get_model("learning", "LearningEventRecord")
    FlashcardReview = apps.get_model("flashcards", "FlashcardReview")
    FlashcardState = apps.get_model("flashcards", "FlashcardState")

    merge_knowledge_sources(apps)
    merge_learning_objects(apps)
    merge_topics(apps)
    merge_league_data(apps)

    LearningEventRecord.objects.filter(product_id__in=LEGACY_PRODUCT_IDS).update(
        product_id=PRODUCT_ID
    )
    FlashcardState.objects.filter(
        schedule_rule_version__in=LEGACY_REVIEW_RULE_VERSIONS
    ).update(schedule_rule_version=REVIEW_RULE_VERSION)
    FlashcardReview.objects.filter(
        rule_version__in=LEGACY_REVIEW_RULE_VERSIONS
    ).update(rule_version=REVIEW_RULE_VERSION)


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0002_phase5_progress_review"),
        ("games", "0005_gamequestion_timer_extended_at_and_more"),
        ("flashcards", "0004_separate_new_cards_from_leitner"),
        ("league", "0002_phase6_league_seasons"),
    ]

    operations = [
        migrations.RunPython(rename_legacy_product, migrations.RunPython.noop),
    ]
