from django.conf import settings
from django.db import models


class CrawlRun(models.Model):
    class Kind(models.TextChoices):
        NEWS = "news", "News"
        PRICES = "prices", "Prices"
        FLOORSHEET = "floorsheet", "Floorsheet"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    kind = models.CharField(max_length=20, choices=Kind.choices)
    portal = models.CharField(max_length=50, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUED,
    )
    items = models.IntegerField(default=0)
    error = models.TextField(blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="crawl_runs",
    )
    celery_task_id = models.CharField(max_length=64, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["status", "-started_at"]),
        ]

    def __str__(self):
        portal = self.portal or "all"
        return f"{self.kind}/{portal} {self.status}"
