from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Article(models.Model):
    url = models.URLField(max_length=600, unique=True)
    portal = models.CharField(max_length=50, db_index=True)
    title = models.TextField()
    body = models.TextField(blank=True)
    raw_date = models.CharField(max_length=60, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    crawled_at = models.DateTimeField(auto_now_add=True)
    categorized = models.BooleanField(default=False)

    class Meta:
        ordering = ["-published_at", "-crawled_at"]
        indexes = [
            models.Index(fields=["-published_at"]),
            models.Index(fields=["portal", "-crawled_at"]),
        ]

    def __str__(self):
        return self.title[:80]


class ArticleTag(models.Model):
    class Source(models.TextChoices):
        AUTO = "auto", "Auto"
        MANUAL = "manual", "Manual"

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="tags")
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="news_tags",
    )
    confidence = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.AUTO)
    matched_on = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["article", "company"],
                name="unique_article_company_tag",
            ),
        ]
        indexes = [
            models.Index(fields=["company", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.article_id} -> {self.company_id}"


class TagCorrection(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="corrections",
    )
    old_tags = models.JSONField()
    new_tags = models.JSONField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tag_corrections",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"correction {self.pk} for article {self.article_id}"
