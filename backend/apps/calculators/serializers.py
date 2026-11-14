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
    """The browse/search list: everything the client groups and searches by.
    Tags are left to the detail view -- the list never shows them, and with
    483 calculators they were a third of this payload."""

    categories = CalculatorCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Calculator
        fields = ["slug", "name", "name_fa", "description", "description_fa", "categories"]


class CalculatorDetailSerializer(CalculatorListSerializer):
    tags = CalculatorTagSerializer(many=True, read_only=True)

    class Meta(CalculatorListSerializer.Meta):
        fields = CalculatorListSerializer.Meta.fields + [
            "tags",
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
