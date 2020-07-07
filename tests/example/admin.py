from django.contrib import admin

from .models import Article, Author


class ArticleInline(admin.TabularInline):
    model = Article


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    inlines = [
        ArticleInline,
    ]
