from django.contrib import admin

from apps.crawling.models import CrawlRun


@admin.register(CrawlRun)
class CrawlRunAdmin(admin.ModelAdmin):
    list_display = ("kind", "portal", "status", "items", "triggered_by", "started_at", "finished_at")
    list_filter = ("kind", "status", "portal")
