from types import SimpleNamespace

from apps.news.categorizer import match_companies
from apps.news.models import Article, ArticleTag


def _company(**kwargs):
    defaults = {"symbol": "NABIL", "name": "Nabil Bank Limited", "aliases": ["Nabil", "Nabil Bank"]}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_symbol_and_alias_match():
    companies = [
        _company(),
        _company(symbol="NTC", name="Nepal Doorsanchar Company Limited", aliases=["Nepal Telecom", "NTC"]),
    ]
    matches = match_companies("Nabil Bank posts higher profit", "No other bank.", companies)
    assert len(matches) == 1
    assert matches[0]["company"].symbol == "NABIL"
    assert matches[0]["confidence"] >= 0.9
    kinds = {item["kind"] for item in matches[0]["matched_on"]}
    assert "alias" in kinds or "name" in kinds


def test_symbol_inside_another_word_does_not_match():
    matches = match_companies("SCNABILX update", "", [_company()])
    assert matches == []


def test_unrelated_text_has_no_tags():
    matches = match_companies("Gold price rises", "Domestic market only.", [_company()])
    assert matches == []


def test_apply_tags_is_idempotent(db):
    from apps.companies.models import Company
    from apps.news.categorizer import categorize_article

    Company.objects.create(
        symbol="NABIL",
        name="Nabil Bank Limited",
        aliases=["Nabil", "Nabil Bank"],
        active=True,
    )
    article = Article.objects.create(
        url="https://example.com/nabil",
        portal="merolagani",
        title="Nabil Bank dividend",
        body="NABIL closed higher.",
    )
    categorize_article(article)
    categorize_article(article)
    assert ArticleTag.objects.filter(article=article, company__symbol="NABIL").count() == 1
    article.refresh_from_db()
    assert article.categorized is True
