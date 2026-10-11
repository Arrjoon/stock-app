import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="apps.analysis.tasks.categorize_article")
def categorize_article(article_id: int) -> None:
    """Hook for Section 2. No-op until categorization is implemented."""
    logger.info("categorize_article stub received article_id=%s", article_id)
