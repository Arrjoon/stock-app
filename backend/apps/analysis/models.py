from django.db import models


class AnalysisResult(models.Model):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="analysis_results",
    )
    date = models.DateField()
    vwap = models.DecimalField(max_digits=12, decimal_places=2)
    close_vs_vwap_pct = models.FloatField()
    pressure = models.FloatField()
    pressure_5d = models.FloatField(null=True, blank=True)
    volume_zscore = models.FloatField(null=True, blank=True)
    is_volume_anomaly = models.BooleanField(default=False)
    news_count = models.IntegerField(default=0)
    next_day_return_pct = models.FloatField(null=True, blank=True)
    next_day_volume_change_pct = models.FloatField(null=True, blank=True)
    top_buyers = models.JSONField(default=list)
    top_sellers = models.JSONField(default=list)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "date"],
                name="unique_analysis_company_date",
            ),
        ]
        indexes = [
            models.Index(fields=["company", "-date"]),
        ]

    def __str__(self):
        return f"{self.company_id} {self.date}"
