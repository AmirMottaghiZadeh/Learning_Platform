from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError

from .selectors import (
    chapter_exam_points,
    get_chapter,
    lesson_groups,
    mark_drug_read,
    topics_for_chapter,
)
from .serializers import (
    ChapterProgressUpdateSerializer,
    ChapterSerializer,
    LessonGroupSerializer,
)


def _chapter_not_found():
    return PlatformAPIError(
        "No lesson chapter for that ATC code.", code="NOT_FOUND", status_code=404
    )


def _chapter_payload(category, ingredients, progress, read_slugs):
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
        "progress": {
            # Globally-read drugs (see apps.lessons.models.ReadDrug), so a
            # drug read via a different chapter it also belongs to (e.g.
            # aspirin under A01/B01/N02) shows as read here too.
            "read_drug_slugs": sorted(read_slugs),
            "scroll_pct": progress.scroll_pct,
            "last_opened_at": progress.last_opened_at,
        },
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
        category, ingredients, progress, read_slugs = result

        body = ChapterProgressUpdateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data

        touched = False
        slug = data.get("drug_slug", "").strip()
        if slug:
            if slug not in {i.slug for i in ingredients}:
                raise PlatformAPIError(
                    "That drug is not in this chapter.",
                    code="INVALID_DRUG",
                    status_code=400,
                )
            if slug not in read_slugs:
                mark_drug_read(request.user, slug)
                read_slugs = {*read_slugs, slug}
            touched = True
        if "scroll_pct" in data:
            progress.scroll_pct = data["scroll_pct"]
            touched = True
        if touched:
            progress.save(update_fields=["scroll_pct", "last_opened_at"])

        return Response(
            ChapterSerializer(_chapter_payload(category, ingredients, progress, read_slugs)).data
        )
