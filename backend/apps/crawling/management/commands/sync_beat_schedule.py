from django.conf import settings
from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, IntervalSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Upsert django-celery-beat PeriodicTask rows from settings."

    def handle(self, *args, **options):
        news_interval, _ = IntervalSchedule.objects.get_or_create(
            every=settings.CRAWL_NEWS_MINUTES,
            period=IntervalSchedule.MINUTES,
        )
        price_cron, _ = CrontabSchedule.objects.get_or_create(
            minute=str(settings.CRAWL_PRICES_MINUTE),
            hour=str(settings.CRAWL_PRICES_HOUR),
            day_of_week="mon-fri",
            day_of_month="*",
            month_of_year="*",
            timezone=settings.TIME_ZONE,
        )
        floorsheet_cron, _ = CrontabSchedule.objects.get_or_create(
            minute=str(settings.CRAWL_FLOORSHEET_MINUTE),
            hour=str(settings.CRAWL_FLOORSHEET_HOUR),
            day_of_week="mon-fri",
            day_of_month="*",
            month_of_year="*",
            timezone=settings.TIME_ZONE,
        )
        analysis_cron, _ = CrontabSchedule.objects.get_or_create(
            minute=str(settings.ANALYSIS_MINUTE),
            hour=str(settings.ANALYSIS_HOUR),
            day_of_week="mon-fri",
            day_of_month="*",
            month_of_year="*",
            timezone=settings.TIME_ZONE,
        )

        specs = [
            (
                "crawl-news-merolagani",
                "apps.news.tasks.crawl_portal_news",
                '["merolagani"]',
                {"interval": news_interval},
            ),
            (
                "crawl-news-sharesansar",
                "apps.news.tasks.crawl_portal_news",
                '["sharesansar"]',
                {"interval": news_interval},
            ),
            (
                "crawl-news-bizmandu",
                "apps.news.tasks.crawl_portal_news",
                '["bizmandu"]',
                {"interval": news_interval},
            ),
            (
                "crawl-prices-after-close",
                "apps.market.tasks.crawl_prices",
                "[]",
                {"crontab": price_cron},
            ),
            (
                "crawl-floorsheet-after-close",
                "apps.market.tasks.crawl_floorsheet",
                "[]",
                {"crontab": floorsheet_cron},
            ),
            (
                "compute-behavior-after-close",
                "apps.analysis.tasks.compute_behavior",
                "[]",
                {"crontab": analysis_cron},
            ),
        ]
        for name, task, args, schedule in specs:
            defaults = {
                "task": task,
                "args": args,
                "enabled": True,
                "interval": schedule.get("interval"),
                "crontab": schedule.get("crontab"),
            }
            PeriodicTask.objects.update_or_create(name=name, defaults=defaults)
            self.stdout.write(f"synced {name}")
