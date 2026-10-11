from django.core.management.base import BaseCommand

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
        articles = Article.objects.all() if options["all"] else Article.objects.filter(categorized=False)
        tagged = 0
        seen = 0
        for article in articles.iterator():
            tagged += categorize_article(article)
            seen += 1
        self.stdout.write(f"categorized {seen} articles, {tagged} automatic tags")
