from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def render_merolagani_list_pages(url: str, max_pages: int, user_agent: str, timeout: float) -> list[str]:
    """Click MeroLagani Load More in Chromium. Returns HTML snapshots."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright is not installed; MeroLagani extra pages skipped")
        return []

    pages_html: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(user_agent=user_agent)
        page.goto(url, wait_until="domcontentloaded", timeout=int(timeout * 1000))
        pages_html.append(page.content())
        for _ in range(max(max_pages - 1, 0)):
            button = page.locator('a[data-load="news-block-three"]')
            if button.count() == 0:
                break
            button.first.click()
            page.wait_for_timeout(1500)
            pages_html.append(page.content())
        browser.close()
    return pages_html
