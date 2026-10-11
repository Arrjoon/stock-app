from __future__ import annotations

import logging
import re
from datetime import datetime

from dateutil import parser as date_parser
from django.utils import timezone

logger = logging.getLogger(__name__)

_TZ = timezone.get_default_timezone()

_ENGLISH_DATE = re.compile(
    r"("
    r"[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}(?:\s+\d{1,2}:\d{2}\s*(?:AM|PM))?"
    r"|"
    r"\d{1,2}\s+[A-Za-z]{3,9},?\s+\d{4}"
    r"|"
    r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2}|Z)?)?"
    r")"
)


def parse_published_at(raw: str | None):
    """Parse a Gregorian date. Return None for Nepali-only or unreadable values."""
    text = (raw or "").strip()
    if not text:
        return None
    match = _ENGLISH_DATE.search(text)
    candidate = match.group(1) if match else text
    try:
        parsed = date_parser.parse(candidate, fuzzy=True)
    except (ValueError, OverflowError, TypeError):
        logger.warning("Could not parse article date %r", raw)
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, _TZ)
    if parsed.year < 2018:
        logger.warning("Ignoring implausible article date %s from %r", parsed, raw)
        return None
    return parsed
