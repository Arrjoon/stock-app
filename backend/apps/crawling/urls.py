from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def normalize_url(url: str) -> str:
    """Strip fragments, utm_* params, and trailing slashes before dedupe."""
    parsed = urlparse((url or "").strip())
    if not parsed.netloc and not parsed.path:
        return ""
    query = urlencode(
        [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.lower().startswith("utm_")
        ]
    )
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    scheme = parsed.scheme.lower() or "https"
    return urlunparse((scheme, parsed.netloc.lower(), path, "", query, ""))
