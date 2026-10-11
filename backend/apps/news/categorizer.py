from __future__ import annotations

import re

from apps.companies.models import Company
from apps.news.models import Article, ArticleTag

SYMBOL_CONFIDENCE = 0.95
NAME_CONFIDENCE = 0.90
ALIAS_CONFIDENCE = 0.80
MIN_CONFIDENCE = 0.80


def match_companies(title: str, body: str, companies) -> list[dict]:
    """Score active companies against title and body. No database writes."""
    text = f"{title or ''}\n{body or ''}"
    found = []
    for company in companies:
        matched_on = []
        confidence = 0.0
        if _contains(text, company.symbol):
            matched_on.append({"term": company.symbol, "kind": "symbol"})
            confidence = max(confidence, SYMBOL_CONFIDENCE)
        if company.name and _contains(text, company.name):
            matched_on.append({"term": company.name, "kind": "name"})
            confidence = max(confidence, NAME_CONFIDENCE)
        for alias in company.aliases or []:
            if alias and _contains(text, alias):
                matched_on.append({"term": alias, "kind": "alias"})
                confidence = max(confidence, ALIAS_CONFIDENCE)
        if matched_on and confidence >= MIN_CONFIDENCE:
            found.append(
                {
                    "company": company,
                    "confidence": confidence,
                    "matched_on": matched_on,
                }
            )
    return found


def categorize_article(article: Article) -> int:
    """Replace automatic tags. Manual tags for the same company are left as-is."""
    companies = list(Company.objects.filter(active=True))
    matches = match_companies(article.title, article.body, companies)
    manual_ids = set(
        ArticleTag.objects.filter(article=article, source=ArticleTag.Source.MANUAL).values_list(
            "company_id", flat=True
        )
    )
    ArticleTag.objects.filter(article=article, source=ArticleTag.Source.AUTO).exclude(
        company_id__in=manual_ids
    ).delete()
    written = 0
    for match in matches:
        company = match["company"]
        if company.id in manual_ids:
            continue
        ArticleTag.objects.update_or_create(
            article=article,
            company=company,
            defaults={
                "confidence": match["confidence"],
                "source": ArticleTag.Source.AUTO,
                "matched_on": match["matched_on"],
            },
        )
        written += 1
    if not article.categorized:
        article.categorized = True
        article.save(update_fields=["categorized"])
    return written


def _contains(text: str, term: str) -> bool:
    cleaned = (term or "").strip()
    if len(cleaned) < 2:
        return False
    pattern = rf"(?<!\w){re.escape(cleaned)}(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None
