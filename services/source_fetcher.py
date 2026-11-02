
import ipaddress
import logging
import re
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

MAX_URLS = 8
MAX_BYTES = 400_000
MAX_TEXT = 10_000
TIMEOUT = 12

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/125.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
}


def safe_url(url):
    """Validate public HTTP/HTTPS URLs and block private IP addresses."""
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        if not parsed.hostname or parsed.username or parsed.password:
            return False

        if parsed.port and parsed.port not in (80, 443):
            return False

        host = parsed.hostname.lower()

        if host == "localhost" or host.endswith(".local"):
            return False

        addresses = socket.getaddrinfo(
            host,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )

        if not addresses:
            return False

        return all(
            ipaddress.ip_address(item[4][0]).is_global
            for item in addresses
        )

    except (ValueError, OSError, socket.gaierror):
        return False


def normalize_url(url):
    if not isinstance(url, str):
        return None

    url = url.strip()

    try:
        parsed = urlparse(url)

        if not parsed.scheme:
            url = "https://" + url
            parsed = urlparse(url)

        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return None

        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path or "/",
            "",
            parsed.query,
            "",
        ))

        return normalized if safe_url(normalized) else None

    except ValueError:
        return None


def discover_sources(question, limit=8):
    """Search DuckDuckGo and return unique external webpage URLs."""
    if not isinstance(question, str) or not question.strip():
        return []

    limit = min(max(int(limit), 0), MAX_URLS)

    if not limit:
        return []

    try:
        response = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": question.strip()},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for link in soup.select(".result__a"):
            href = link.get("href", "")
            parsed = urlparse(href)

            if "duckduckgo.com" in (parsed.hostname or ""):
                href = parse_qs(parsed.query).get("uddg", [""])[0]

            url = normalize_url(href)

            if url and url not in results:
                results.append(url)

            if len(results) >= limit:
                break

        return results

    except Exception:
        logger.exception("Source discovery failed")
        return []


def extract_page_text(html):
    """Extract article-like text while removing common page boilerplate."""
    soup = BeautifulSoup(html, "html.parser")

    for element in soup([
        "script", "style", "noscript", "svg", "iframe",
        "nav", "footer", "header", "aside", "form",
        "button", "input", "select", "textarea",
    ]):
        element.decompose()

    unwanted = re.compile(
        r"advert|cookie|newsletter|social|share|"
        r"breadcrumb|pagination|sidebar|navigation|"
        r"related-post|comment|popup|subscribe",
        re.I,
    )

    for element in list(soup.find_all(True)):
        identity = " ".join([
            str(element.get("id", "")),
            " ".join(element.get("class", [])),
            str(element.get("role", "")),
        ])

        if unwanted.search(identity):
            element.decompose()

    article = (
        soup.find("article")
        or soup.find("main")
        or soup.find(attrs={"role": "main"})
        or soup.body
        or soup
    )

    blocks = article.find_all([
        "h1", "h2", "h3", "h4", "p", "li", "blockquote"
    ])

    lines = []
    seen = set()

    for block in blocks:
        text = re.sub(r"\s+", " ", block.get_text(" ", strip=True))

        if len(text) < 40 or text in seen:
            continue

        seen.add(text)
        lines.append(text)

    if not lines:
        raw = article.get_text("\n", strip=True)
        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in raw.splitlines()
            if len(line.strip()) >= 40
        ]

    return "\n".join(lines)[:MAX_TEXT]


def fetch_single_source(url):
    clean_url = normalize_url(url)

    if not clean_url:
        return {
            "url": url,
            "status": "error",
            "text": "",
            "error": "Invalid or unsafe URL.",
        }

    try:
        with requests.get(
            clean_url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=False,
            stream=True,
        ) as response:

            if response.status_code in (301, 302, 303, 307, 308):
                return {
                    "url": clean_url,
                    "status": "error",
                    "text": "",
                    "error": "Website redirected the request.",
                }

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type", ""
            ).lower()

            if not any(
                value in content_type
                for value in ("text/html", "application/xhtml+xml")
            ):
                return {
                    "url": clean_url,
                    "status": "error",
                    "text": "",
                    "error": "Not an HTML webpage.",
                }

            content = bytearray()

            for chunk in response.iter_content(8192):
                content.extend(chunk)

                if len(content) > MAX_BYTES:
                    return {
                        "url": clean_url,
                        "status": "error",
                        "text": "",
                        "error": "Webpage exceeded size limit.",
                    }

        html = bytes(content).decode("utf-8", errors="replace")
        text = extract_page_text(html)

        if len(text) < 80:
            return {
                "url": clean_url,
                "status": "error",
                "text": "",
                "error": "Insufficient readable article content.",
            }

        title_soup = BeautifulSoup(html, "html.parser")
        title_tag = title_soup.find("title")

        return {
            "url": clean_url,
            "title": (
                title_tag.get_text(" ", strip=True)[:200]
                if title_tag else clean_url
            ),
            "status": "success",
            "text": text,
        }

    except requests.HTTPError as error:
        status = error.response.status_code if error.response else "unknown"
        message = f"HTTP error: {status}"

    except requests.Timeout:
        message = "Request timed out."

    except requests.RequestException:
        message = "Unable to access webpage."

    except Exception:
        logger.exception("Source extraction failed")
        message = "Content extraction failed."

    return {
        "url": clean_url,
        "status": "error",
        "text": "",
        "error": message,
    }


def fetch_sources(urls):
    """Fetch up to eight unique webpages concurrently."""
    if not isinstance(urls, list):
        return []

    unique = []
    seen = set()

    for url in urls:
        if not isinstance(url, str):
            continue

        key = url.strip()

        if key and key not in seen:
            seen.add(key)
            unique.append(key)

        if len(unique) >= MAX_URLS:
            break

    results = [None] * len(unique)

    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = {
            executor.submit(fetch_single_source, url): index
            for index, url in enumerate(unique)
        }

        for future in as_completed(tasks):
            index = tasks[future]

            try:
                results[index] = future.result()
            except Exception:
                results[index] = {
                    "url": unique[index],
                    "status": "error",
                    "text": "",
                    "error": "Source processing failed.",
                }

    return results
