from rest_framework import serializers
from .models import Drug, DrugTopic, DrugQuestionSource
from .services import build_options

class DrugTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrugTopic
        fields = ["key", "label", "detail"]


class TargetCategorySerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    count = serializers.IntegerField()

class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drug
        fields = ["id", "external_id", "name", "persian_name", "brand_name", "generic_name", "dosage_form", "drug_classification"]

class QuestionSourceSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()
    class Meta:
        model = DrugQuestionSource
        fields = ["id", "question_type", "prompt", "subtitle", "chip", "options"]
    def get_options(self, obj):
        return build_options(obj)
