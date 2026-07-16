import random

from django.db.models import Max, Min

from apps.learning.contracts import (
    KnowledgeSourceRef,
    LearningObjectRef,
    LearningTopicRef,
)
from apps.learning.models import KnowledgeSource
from apps.quizzes.contracts import QuestionGenerationContext

from .learning_sync import (
    PRODUCT_ID,
    drug_question_source_external_id,
    sync_drug_question_source,
    sync_drug_question_sources,
)
from .categories import category_payload_for_drug
from .models import DrugQuestionSource
from .services import INVALID_ANSWERS, is_valid_correct_answer


MIN_QUIZ_SOURCE_CANDIDATES = 40
QUIZ_SOURCE_CANDIDATE_FACTOR = 8
MAX_QUIZ_SOURCE_CANDIDATES = 400


class PharmexaLearningAdapter:
    product_id = PRODUCT_ID

    def list_knowledge_sources(
        self,
        context: QuestionGenerationContext,
    ) -> list[KnowledgeSourceRef]:
        synced_sources = self._list_synced_knowledge_sources(context)
        return [self._generic_to_knowledge_source_ref(source) for source in synced_sources]

    def get_source_instance(self, knowledge_source_id: int) -> KnowledgeSource:
        try:
            return KnowledgeSource.objects.get(id=knowledge_source_id, product_id=self.product_id)
        except KnowledgeSource.DoesNotExist:
            legacy_source = DrugQuestionSource.objects.get(id=knowledge_source_id)
            return sync_drug_question_source(legacy_source)

    def get_source_instances(self, knowledge_source_ids: list[int]) -> dict[int, KnowledgeSource]:
        queryset = (
            KnowledgeSource.objects
            .filter(id__in=knowledge_source_ids, product_id=self.product_id)
            .select_related("learning_object", "topic")
        )
        return {source.id: source for source in queryset}

    def get_knowledge_source_for_legacy_source(self, source: DrugQuestionSource) -> KnowledgeSource:
        external_id = drug_question_source_external_id(source)
        try:
            return KnowledgeSource.objects.get(product_id=self.product_id, external_id=external_id)
        except KnowledgeSource.DoesNotExist:
            return sync_drug_question_source(source)

    def _list_synced_knowledge_sources(
        self,
        context: QuestionGenerationContext,
    ) -> list[KnowledgeSource]:
        queryset = (
            KnowledgeSource.objects
            .filter(product_id=self.product_id, is_active=True)
            .exclude(prompt="")
            .exclude(correct_answer="")
            .exclude(correct_answer__in=INVALID_ANSWERS)
            .select_related("learning_object", "topic")
        )

        if context.topic_key and context.topic_key != "random":
            queryset = queryset.filter(topic__key=context.topic_key)
        if context.target_category_key:
            queryset = queryset.filter(metadata__target_category_key=context.target_category_key)

        candidate_limit = min(
            MAX_QUIZ_SOURCE_CANDIDATES,
            max(
                MIN_QUIZ_SOURCE_CANDIDATES,
                context.question_count * QUIZ_SOURCE_CANDIDATE_FACTOR,
            ),
        )
        total = queryset.count()
        if total <= candidate_limit:
            sources = list(queryset.order_by("id"))
        else:
            bounds = queryset.aggregate(
                minimum_id=Min("id"),
                maximum_id=Max("id"),
            )
            anchor_id = random.randint(bounds["minimum_id"], bounds["maximum_id"])
            sources = list(
                queryset.filter(id__gte=anchor_id).order_by("id")[:candidate_limit]
            )
            if len(sources) < candidate_limit:
                sources.extend(
                    queryset.filter(id__lt=anchor_id).order_by("id")[
                        :candidate_limit - len(sources)
                    ]
                )
        return [source for source in sources if is_valid_correct_answer(source.correct_answer)]

    def _generic_to_knowledge_source_ref(self, source: KnowledgeSource) -> KnowledgeSourceRef:
        return KnowledgeSourceRef(
            id=source.id,
            source_type=source.source_type,
            prompt=source.prompt,
            correct_answer=source.correct_answer,
            topic=LearningTopicRef(
                key=source.topic.key,
                label=source.topic.label,
            ),
            learning_object=LearningObjectRef(
                id=source.learning_object_id,
                display_name=source.learning_object.display_name,
                subtitle=source.learning_object.subtitle,
                metadata=source.learning_object.metadata,
            ),
            explanation=source.explanation,
            metadata=source.metadata,
        )

    def _to_knowledge_source_ref(self, source: DrugQuestionSource) -> KnowledgeSourceRef:
        drug = source.drug
        category_payload = category_payload_for_drug(drug)
        display_name = (
            drug.brand_name
            or drug.name
            or drug.persian_name
            or drug.external_id
        )

        return KnowledgeSourceRef(
            id=source.id,
            source_type=source.question_type,
            prompt=source.prompt,
            correct_answer=source.correct_answer,
            topic=LearningTopicRef(
                key=source.topic.key,
                label=source.topic.label,
            ),
            learning_object=LearningObjectRef(
                id=drug.id,
                display_name=display_name,
                subtitle=drug.generic_name or drug.drug_classification,
                metadata={
                    "external_id": drug.external_id,
                    "source_file": drug.source_file,
                    **category_payload,
                },
            ),
            explanation=source.feedback,
            metadata={
                "subtitle": source.subtitle,
                "chip": source.chip,
                **category_payload,
            },
        )


class KGameLearningAdapter(PharmexaLearningAdapter):
    pass
