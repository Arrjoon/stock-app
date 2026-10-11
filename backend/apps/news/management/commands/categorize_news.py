from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from apps.news.categorizer import categorize_article
from apps.news.models import Article


class Command(BaseCommand):
    help = "Tag uncategorized articles to active companies."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Re-tag every article, not only uncategorized ones.",
        )

    def handle(self, *args, **options):
        if options["all"]:
            articles = Article.objects.all()
        else:
            articles = Article.objects.annotate(tag_count=Count("tags")).filter(Q(categorized=False) | Q(tag_count=0))
        tagged = 0
        seen = 0
        for article in articles.iterator():
            tagged += categorize_article(article)
            seen += 1
        self.stdout.write(f"categorized {seen} articles, {tagged} automatic tags")
