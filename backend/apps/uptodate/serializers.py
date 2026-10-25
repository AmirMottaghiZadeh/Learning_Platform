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
    # Always empty: the search reads titles only. Kept for app builds up to
    # 0.1.0, which show it under the title when it has text.
    snippet = serializers.CharField(allow_blank=True)
    # The title-word starts the query was matched with -- what the app
    # highlights in the title.
    terms = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    # The query with its misspelt words corrected; "" when none was.
    corrected = serializers.CharField(allow_blank=True, required=False, default="")


class UptodateArticleSerializer(UptodateTopicSerializer):
    contributors = serializers.ListField(child=serializers.CharField())
    outline_html = serializers.CharField(allow_blank=True)
    body_html = serializers.CharField(allow_blank=True)


class UptodateImageSerializer(serializers.Serializer):
    id = serializers.CharField()
    content_type = serializers.CharField()
    data_base64 = serializers.CharField()
