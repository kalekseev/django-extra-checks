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


class DisableCheckSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField()

    def method_with_meta_class(self):
        class Meta:
            ...

    # extra-checks-disable-next-line drf-model-serializer-extra-kwargs
    class Meta:
        model = Author
        extra_kwargs = {"first_name": {"read_only": True}}
