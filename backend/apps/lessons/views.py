from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError

from .selectors import chapter_exam_points, get_chapter, lesson_groups, topics_for_chapter
from .serializers import (
    ChapterProgressUpdateSerializer,
    ChapterSerializer,
    LessonGroupSerializer,
)


def _chapter_not_found():
    return PlatformAPIError(
        "No lesson chapter for that ATC code.", code="NOT_FOUND", status_code=404
    )


def _chapter_payload(category, ingredients, progress):
    topics = topics_for_chapter(category.code, category.parent)
    primary = topics[0] if topics else {"code": "", "name_fa": "", "name_en": ""}
    return {
        "code": category.code,
        "name_fa": category.name_fa,
        "name_en": category.name_en,
        # Primary study topic (see apps.lessons.data.study_topics) — what the
        # learner actually browsed by, e.g. "Hypertension" rather than the raw
        # ATC anatomical parent.
        "group_code": primary["code"],
        "group_name_fa": primary["name_fa"],
        "group_name_en": primary["name_en"],
        # Every topic this chapter belongs to (a class like beta blockers is
        # legitimately first-line in more than one), for a "also relevant to"
        # display.
        "topics": topics,
        # The true, unmodified ATC anatomical (L1) group, kept for rigour.
        "anatomical_name_fa": category.parent.name_fa if category.parent else "",
        "anatomical_name_en": category.parent.name_en if category.parent else "",
        "drugs": list(ingredients),
        "exam_points": chapter_exam_points(ingredients),
        "progress": progress,
    }


class LessonGroupsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=LessonGroupSerializer(many=True))
    def get(self, request):
        return Response(LessonGroupSerializer(lesson_groups(request.user), many=True).data)


class ChapterView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ChapterSerializer)
    def get(self, request, atc_code):
        result = get_chapter(request.user, atc_code)
        if result is None:
            raise _chapter_not_found()
        return Response(ChapterSerializer(_chapter_payload(*result)).data)

    @extend_schema(request=ChapterProgressUpdateSerializer, responses=ChapterSerializer)
    def post(self, request, atc_code):
        result = get_chapter(request.user, atc_code)
        if result is None:
            raise _chapter_not_found()
        category, ingredients, progress = result

        body = ChapterProgressUpdateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data

        changed = []
        slug = data.get("drug_slug", "").strip()
        if slug:
            if slug not in {i.slug for i in ingredients}:
                raise PlatformAPIError(
                    "That drug is not in this chapter.",
                    code="INVALID_DRUG",
                    status_code=400,
                )
            if slug not in progress.read_drug_slugs:
                progress.mark_read(slug)
                changed.append("read_drug_slugs")
        if "scroll_pct" in data:
            progress.scroll_pct = data["scroll_pct"]
            changed.append("scroll_pct")
        if changed:
            progress.save(update_fields=[*changed, "last_opened_at"])

        return Response(ChapterSerializer(_chapter_payload(category, ingredients, progress)).data)
