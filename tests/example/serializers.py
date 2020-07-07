from rest_framework import serializers

from .models import Article, Author


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        read_only_fields: list = []


class AuthorSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField()

    class Meta:
        model = Author
        extra_kwargs = {"first_name": {"read_only": True}}


class ModernAuthorSerializer(AuthorSerializer):
    first_name = serializers.CharField()

    class Meta:
        model = Author
        extra_kwargs = {"first_name": {"read_only": True}}
