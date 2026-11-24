"""Fetch and extract the main text from a public article URL."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import requests
import trafilatura
from bs4 import BeautifulSoup

MAX_PAGE_BYTES = 5 * 1024 * 1024
MAX_ARTICLE_CHARS = 14_000
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
USER_AGENT = "Week2ContentRepurposer/1.0 (article text extraction; educational project)"


class ArticleExtractionError(ValueError):
    """Raised when an article cannot be fetched or meaningfully extracted."""


def validate_public_url(url: str) -> str:
    """Validate an HTTP(S) URL and reject hosts resolving to non-public IPs."""
    candidate = (url or "").strip()
    try:
        parsed = urlsplit(candidate)
        port = parsed.port
    except ValueError as exc:
        raise ArticleExtractionError("That URL does not look valid. Check it and try again.") from exc

    if parsed.scheme.lower() not in {"http", "https"}:
        raise ArticleExtractionError("Use a normal http:// or https:// article URL.")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ArticleExtractionError("Enter a public article URL without login details.")
    if port not in {None, 80, 443}:
        raise ArticleExtractionError("For safety, this app only fetches standard web ports (80 and 443).")

    host = parsed.hostname.rstrip(".")
    try:
        addresses = {ipaddress.ip_address(host)}
    except ValueError:
        try:
            resolved = socket.getaddrinfo(host, port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
            addresses = {ipaddress.ip_address(item[4][0]) for item in resolved}
        except (OSError, ValueError) as exc:
            raise ArticleExtractionError("The website could not be reached or its domain could not be resolved.") from exc

    if not addresses or any(not address.is_global for address in addresses):
        raise ArticleExtractionError("This app only fetches public websites, not localhost or private network addresses.")

    return candidate


def _download_html(url: str) -> tuple[str, str]:
    current_url = url
    session = requests.Session()
    # Avoid inheriting proxy settings from the machine running the app.
    session.trust_env = False
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
    }

    try:
        for _ in range(6):
            current_url = validate_public_url(current_url)
            response = session.get(
                current_url,
                headers=headers,
                timeout=(6, 18),
                allow_redirects=False,
                stream=True,
            )

            if response.status_code in REDIRECT_STATUSES:
                location = response.headers.get("Location")
                response.close()
                if not location:
                    raise ArticleExtractionError("The website returned a redirect without a destination.")
                current_url = urljoin(current_url, location)
                continue

            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if content_type and not any(kind in content_type for kind in ("text/html", "application/xhtml+xml")):
                response.close()
                raise ArticleExtractionError("That link does not appear to point to an HTML article page.")

            chunks: list[bytes] = []
            total_bytes = 0
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                total_bytes += len(chunk)
                if total_bytes > MAX_PAGE_BYTES:
                    response.close()
                    raise ArticleExtractionError("This page is larger than the 5 MB limit.")
                chunks.append(chunk)

            encoding = response.encoding or "utf-8"
            response.close()
            return b"".join(chunks).decode(encoding, errors="replace"), current_url

        raise ArticleExtractionError("The page redirected too many times.")
    except ArticleExtractionError:
        raise
    except requests.RequestException as exc:
        raise ArticleExtractionError("The page could not be downloaded. It may block automated requests or be temporarily unavailable.") from exc
    finally:
        session.close()


def _fallback_extract(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled article"

    for element in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "form", "svg"]):
        element.decompose()

    main = soup.find("article") or soup.find("main") or soup.body or soup
    paragraphs = [node.get_text(" ", strip=True) for node in main.find_all(["h1", "h2", "h3", "p", "li"])]
    text = "\n\n".join(part for part in paragraphs if len(part) > 35)
    return title, text


def extract_article(url: str) -> dict[str, str]:
    """Return title, extracted article text and the final URL after redirects."""
    html, final_url = _download_html(url)
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled article"

    extracted = trafilatura.extract(
        html,
        url=final_url,
        include_comments=False,
        include_tables=True,
        favor_precision=True,
    )

    if not extracted or len(extracted.strip()) < 250:
        fallback_title, fallback_text = _fallback_extract(html)
        title = fallback_title or title
        extracted = fallback_text

    cleaned_text = "\n\n".join(line.strip() for line in extracted.splitlines() if line.strip()) if extracted else ""
    if len(cleaned_text) < 250:
        raise ArticleExtractionError(
            "I could not find enough article text on that page. Try a standard blog/article URL rather than a homepage, login page, or JavaScript-only page."
        )

    return {
        "title": title[:300],
        "text": cleaned_text[:MAX_ARTICLE_CHARS],
        "url": final_url,
    }
