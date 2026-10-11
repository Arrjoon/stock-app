from django.core.management.base import BaseCommand, CommandError

from apps.crawling.models import CrawlRun
from apps.market.tasks import crawl_floorsheet, crawl_prices
from apps.news.tasks import crawl_portal_news


class Command(BaseCommand):
    help = "Enqueue the same Celery crawl tasks used by Beat."

    def add_arguments(self, parser):
        parser.add_argument("--kind", choices=["news", "prices", "floorsheet"], required=True)
        parser.add_argument("--portal", default="")

    def handle(self, *args, **options):
        kind = options["kind"]
        portal = options["portal"]
        if kind == "news":
            if not portal:
                raise CommandError("Pass --portal merolagani|sharesansar|bizmandu")
            run = CrawlRun.objects.create(kind=CrawlRun.Kind.NEWS, portal=portal)
            result = crawl_portal_news.delay(portal, run.id)
        elif kind == "prices":
            run = CrawlRun.objects.create(kind=CrawlRun.Kind.PRICES, portal="nepse")
            result = crawl_prices.delay(run.id)
        else:
            run = CrawlRun.objects.create(kind=CrawlRun.Kind.FLOORSHEET, portal="nepse")
            result = crawl_floorsheet.delay(run.id)
        run.celery_task_id = result.id or ""
        run.save(update_fields=["celery_task_id"])
        self.stdout.write(f"queued {kind} {portal or 'all'} run={run.pk} task={result.id}")
