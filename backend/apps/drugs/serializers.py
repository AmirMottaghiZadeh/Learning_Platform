from rest_framework import serializers
from .models import Drug, DrugDatasetDocument, DrugTopic, DrugQuestionSource
from .services import build_options

class DrugTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrugTopic
        fields = ["id", "key", "label", "detail"]


class TargetCategorySerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    count = serializers.IntegerField()


class DrugDatasetDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrugDatasetDocument
        fields = [
            "schema_version",
            "source_file",
            "source_format",
            "source_size_bytes",
            "source_sha256",
            "source_metadata",
            "extraction_metadata",
            "warnings",
            "enrichment_metadata",
            "imported_at",
            "updated_at",
        ]


class DrugSerializer(serializers.ModelSerializer):
    dataset_document = DrugDatasetDocumentSerializer(read_only=True)

    class Meta:
        model = Drug
        fields = [
            "id",
            "external_id",
            "name",
            "persian_name",
            "brand_name",
            "generic_name",
            "dosage_form",
            "drug_classification",
            "dosing_and_administration",
            "consumption_time",
            "consumption_time_sorted",
            "pregnancy",
            "breastfeeding",
            "dose_adjustment",
            "indication",
            "side_effects",
            "clinical_notes",
            "atc_codes",
            "atc_classes",
            "atc_subclasses",
            "atc_categories",
            "category",
            "source_file",
            "source_table",
            "source_row",
            "extra_attributes",
            "dataset_document",
        ]

class QuestionSourceSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()
    class Meta:
        model = DrugQuestionSource
        fields = ["id", "question_type", "prompt", "subtitle", "chip", "options"]
    def get_options(self, obj):
        return build_options(obj)
