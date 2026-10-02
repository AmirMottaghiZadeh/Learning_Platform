from rest_framework import serializers

from .models import Calculator


class CalculatorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calculator
        fields = ["slug", "name", "description", "categories", "tags"]


class CalculatorDetailSerializer(CalculatorListSerializer):
    class Meta(CalculatorListSerializer.Meta):
        fields = CalculatorListSerializer.Meta.fields + [
            "about",
            "author",
            "questions",
            "results",
            "references",
        ]
