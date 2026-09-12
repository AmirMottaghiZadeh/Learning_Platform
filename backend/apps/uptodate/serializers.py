from rest_framework import serializers


class UptodateTopicSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    section = serializers.CharField(allow_blank=True)
    version = serializers.CharField(allow_blank=True)


class UptodateArticleSerializer(UptodateTopicSerializer):
    contributors = serializers.ListField(child=serializers.CharField())
    outline_html = serializers.CharField(allow_blank=True)
    body_html = serializers.CharField(allow_blank=True)


class UptodateImageSerializer(serializers.Serializer):
    id = serializers.CharField()
    content_type = serializers.CharField()
    data_base64 = serializers.CharField()
