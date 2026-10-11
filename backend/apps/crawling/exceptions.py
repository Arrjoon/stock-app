class CrawlerError(Exception):
    """Base crawler failure."""


class RobotsDisallowedError(CrawlerError):
    """Request blocked by the portal robots.txt."""


class PortalDisabledError(CrawlerError):
    """Portal is disabled in CRAWLER_CONFIG."""


class ParseError(CrawlerError):
    """HTML or payload could not be parsed."""
