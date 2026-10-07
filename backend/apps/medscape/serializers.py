import base64

from rest_framework import serializers

from .models import Article, ArticleImage


class ArticleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["slug", "title", "kind", "latest_update"]


class ArticleDetailSerializer(ArticleListSerializer):
    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + ["meta", "url", "categories", "sections"]


class ArticleImageSerializer(serializers.ModelSerializer):
    data_base64 = serializers.SerializerMethodField()

    class Meta:
        model = ArticleImage
        fields = ["id", "content_type", "data_base64"]

    def get_data_base64(self, obj):
        return base64.b64encode(obj.data).decode("ascii")
