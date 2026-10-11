import logging

from celery import shared_task

from apps.analysis.compute import compute_active_companies
from apps.news.categorizer import categorize_article as apply_categories
from apps.news.models import Article
from apps.realtime.notify import publish_update

logger = logging.getLogger(__name__)


@shared_task(name="apps.analysis.tasks.categorize_article")
def categorize_article(article_id: int) -> int:
    article = Article.objects.filter(pk=article_id).first()
    if article is None:
        logger.warning("categorize_article missing article_id=%s", article_id)
        return 0
    written = apply_categories(article)
    company_ids = list(article.tags.values_list("company_id", flat=True))
    publish_update("article.categorized", article_id=article.id, company_ids=company_ids)
    logger.info("categorized article_id=%s tags=%s", article_id, written)
    return written


@shared_task(name="apps.analysis.tasks.compute_behavior")
def compute_behavior() -> int:
    written = compute_active_companies()
    publish_update("analysis.updated", rows=written)
    logger.info("computed behavior rows=%s", written)
    return written
