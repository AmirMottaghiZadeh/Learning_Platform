"""Auth-protected source data; patient inputs and dose calculations stay on device."""

import json
from functools import lru_cache
from pathlib import Path

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.enforcement import require_feature

PEDIATRIC_DOSE_SLUG = "pediatric-dose"


@lru_cache(maxsize=1)
def pediatric_dataset():
    data = json.loads((Path(__file__).parent / "data" / "pediatric-dose.json").read_text(encoding="utf-8"))
    return {"schema_version": 1, **data}


class PediatricDoseDatasetView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=inline_serializer(name="PediatricDoseDataset", fields={
        "schema_version": serializers.IntegerField(),
        "engine_sha256": serializers.CharField(),
        "source": serializers.CharField(),
        "drugs": serializers.ListField(child=serializers.DictField()),
    }))
    def get(self, request):
        require_feature(request, "calculators", item=PEDIATRIC_DOSE_SLUG, consume=True)
        response = Response(pediatric_dataset())
        response["Cache-Control"] = "private, no-store"
        return response
