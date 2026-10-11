from apps.crawling.exceptions import PortalDisabledError
from apps.news.crawlers.bizmandu import BizmanduCrawler
from apps.news.crawlers.merolagani import MeroLaganiCrawler
from apps.news.crawlers.sharesansar import ShareSansarCrawler

CRAWLERS = {
    "merolagani": MeroLaganiCrawler,
    "sharesansar": ShareSansarCrawler,
    "bizmandu": BizmanduCrawler,
}


def get_crawler(portal: str, **kwargs):
    try:
        cls = CRAWLERS[portal]
    except KeyError as exc:
        raise PortalDisabledError(f"No crawler registered for {portal}") from exc
    return cls(**kwargs)
