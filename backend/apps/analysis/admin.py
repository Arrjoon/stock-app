from django.contrib import admin

from apps.analysis.models import AnalysisResult


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ("company", "date", "vwap", "is_volume_anomaly", "news_count", "computed_at")
    list_filter = ("is_volume_anomaly",)
