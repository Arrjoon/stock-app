from django.contrib import admin

from apps.news.models import Article, ArticleTag, TagCorrection


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "portal", "published_at", "categorized", "crawled_at")
    list_filter = ("portal", "categorized")
    search_fields = ("title", "url")


@admin.register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    list_display = ("article", "company", "confidence", "source", "created_at")
    list_filter = ("source",)


@admin.register(TagCorrection)
class TagCorrectionAdmin(admin.ModelAdmin):
    list_display = ("article", "user", "created_at")
