from rest_framework import serializers


class UptodateTopicSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    section = serializers.CharField(allow_blank=True)
    version = serializers.CharField(allow_blank=True)
    # "Feb 11, 2026" -- the topic's own last-updated date, or "" when the
    # header doesn't carry one.
    updated = serializers.CharField(allow_blank=True, required=False, default="")


class UptodateSearchResultSerializer(UptodateTopicSerializer):
    # Plain text around the first query hit in the article body.
    snippet = serializers.CharField(allow_blank=True)


class UptodateArticleSerializer(UptodateTopicSerializer):
    contributors = serializers.ListField(child=serializers.CharField())
    outline_html = serializers.CharField(allow_blank=True)
    body_html = serializers.CharField(allow_blank=True)


class UptodateImageSerializer(serializers.Serializer):
    id = serializers.CharField()
    content_type = serializers.CharField()
    data_base64 = serializers.CharField()
