from rest_framework import serializers


class LexicompDrugSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    generic_id = serializers.IntegerField()
    kind = serializers.ChoiceField(choices=["generic", "brand"])


class InteractionCheckRequestSerializer(serializers.Serializer):
    generic_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=2, max_length=20
    )


class LexicompInteractionSerializer(serializers.Serializer):
    monograph_id = serializers.IntegerField()
    drug_ids = serializers.ListField(child=serializers.IntegerField())
    object_generic_id = serializers.IntegerField()
    object_name = serializers.CharField()
    precipitant_generic_id = serializers.IntegerField()
    precipitant_name = serializers.CharField()
    severity = serializers.CharField()
    reliability = serializers.CharField(allow_blank=True)
    summary = serializers.CharField(allow_blank=True)
    management = serializers.CharField(allow_blank=True)
    discussion = serializers.CharField(allow_blank=True)
    footnotes = serializers.CharField(allow_blank=True)
