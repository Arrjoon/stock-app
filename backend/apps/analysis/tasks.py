import logging

from celery import shared_task

from apps.news.categorizer import categorize_article as apply_categories
from apps.news.models import Article

logger = logging.getLogger(__name__)


@shared_task(name="apps.analysis.tasks.categorize_article")
def categorize_article(article_id: int) -> int:
    article = Article.objects.filter(pk=article_id).first()
    if article is None:
        logger.warning("categorize_article missing article_id=%s", article_id)
        return 0
    written = apply_categories(article)
    logger.info("categorized article_id=%s tags=%s", article_id, written)
    return written
