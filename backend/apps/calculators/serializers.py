from rest_framework import serializers

from .models import Calculator, CalculatorCategory, CalculatorTag


class CalculatorCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculatorCategory
        fields = ["id", "name", "name_fa", "parent_id", "is_main_category"]


class CalculatorTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculatorTag
        fields = ["id", "name", "name_fa"]


class CalculatorListSerializer(serializers.ModelSerializer):
    categories = CalculatorCategorySerializer(many=True, read_only=True)
    tags = CalculatorTagSerializer(many=True, read_only=True)

    class Meta:
        model = Calculator
        fields = ["slug", "name", "name_fa", "description", "description_fa", "categories", "tags"]


class CalculatorDetailSerializer(CalculatorListSerializer):
    class Meta(CalculatorListSerializer.Meta):
        fields = CalculatorListSerializer.Meta.fields + [
            "url",
            "about",
            "about_fa",
            "disclaimer_footer",
            "disclaimer_footer_fa",
            "questions",
            "results",
            "error_checks",
            "formula_strings_fa",
            "references",
        ]
