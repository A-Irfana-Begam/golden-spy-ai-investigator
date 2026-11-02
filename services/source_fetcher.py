
import ipaddress
import logging
import re
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

MAX_URLS = 8
MAX_CONTENT_LENGTH = 500_000
MAX_TEXT_LENGTH = 8_000
REQUEST_TIMEOUT = 12

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
}


def is_safe_url(url):
    """Allow public HTTP/HTTPS URLs and block private network targets."""

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        if not parsed.hostname:
            return False

        if parsed.username or parsed.password:
            return False

        if parsed.port and parsed.port not in (80, 443):
            return False

        hostname = parsed.hostname.lower()

        if hostname in ("localhost",):
            return False

        addresses = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )

        if not addresses:
            return False

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])

            if not ip.is_global:
                return False

        return True

    except (ValueError, socket.gaierror, OSError):
        return False


def normalize_url(url):
    """Normalize and validate a webpage URL."""

    if not isinstance(url, str):
        return None

    url = url.strip()

    if not url:
        return None

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return None

        if not parsed.hostname:
            return None

        if parsed.username or parsed.password:
            return None

        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path or "/",
            "",
            parsed.query,
            "",
        ))

        if not is_safe_url(normalized):
            return None

        return normalized

    except ValueError:
        return None


def discover_sources(question, limit=8):
    """Discover webpage URLs using DuckDuckGo HTML search."""

    if not isinstance(question, str) or not question.strip():
        return []

    limit = max(0, min(int(limit), MAX_URLS))

    if limit == 0:
        return []

    search_url = "https://html.duckduckgo.com/html/"

    try:
        response = requests.post(
            search_url,
            data={"q": question.strip()},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for link in soup.select(".result__a"):
            href = link.get("href", "")

            if not href:
                continue

            # DuckDuckGo may return redirect URLs.
            parsed = urlparse(href)

            if "duckduckgo.com" in (parsed.hostname or ""):
                from urllib.parse import parse_qs

                target = parse_qs(parsed.query).get("uddg", [])

                if target:
                    href = target[0]

            clean_url = normalize_url(href)

            if clean_url and clean_url not in results:
                results.append(clean_url)

            if len(results) >= limit:
                break

        return results

    except requests.RequestException:
        logger.warning("Source discovery failed.")
        return []

    except Exception:
        logger.exception("Unexpected source discovery error.")
        return []


def extract_page_text(html):
    """Extract readable main content and remove webpage boilerplate."""

    soup = BeautifulSoup(html, "html.parser")

    # Remove elements that do not contain useful article content.
    for element in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "iframe",
        "form",
        "button",
        "input",
        "select",
        "textarea",
        "nav",
        "footer",
        "header",
        "aside",
    ]):
        element.decompose()

    # Remove common navigation, advertisement and social elements.
    unwanted_patterns = re.compile(
        r"nav|menu|footer|header|sidebar|advert|ads|"
        r"cookie|popup|modal|social|share|newsletter|"
        r"breadcrumb|pagination|related|recommend|"
        r"comment|subscribe|promotion",
        re.IGNORECASE,
    )

    for element in soup.find_all(True):
        attributes = " ".join([
            str(element.get("id", "")),
            " ".join(element.get("class", [])),
            str(element.get("role", "")),
        ])

        if unwanted_patterns.search(attributes):
            element.decompose()

    # Prefer the main article or main content container.
    main_content = (
        soup.find("article")
        or soup.find("main")
        or soup.find(attrs={"role": "main"})
        or soup.body
        or soup
    )

    # Extract meaningful text blocks.
    content_tags = main_content.find_all([
        "h1", "h2", "h3", "h4",
        "p", "li", "blockquote",
    ])

    lines = []

    for element in content_tags:
        text = element.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text)

        if len(text) < 35:
            continue

        if text not in lines:
            lines.append(text)

    # Fallback for pages without normal article elements.
    if not lines:
        fallback = main_content.get_text("\n", strip=True)

        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in fallback.splitlines()
            if len(line.strip()) >= 35
        ]

    return "\n".join(lines)[:MAX_TEXT_LENGTH]


def fetch_single_source(url):
    """Fetch and extract one webpage."""

    clean_url = normalize_url(url)

    if not clean_url:
        return {
            "url": url,
            "status": "error",
            "text": "",
            "error": "Invalid or unsafe URL.",
        }

    try:
        response = requests.get(
            clean_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
            stream=True,
        )

        if response.status_code in (301, 302, 303, 307, 308):
            return {
                "url": clean_url,
                "status": "error",
                "text": "",
                "error": "Redirected webpage is not supported.",
            }

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            return {
                "url": clean_url,
                "status": "error",
                "text": "",
                "error": "URL does not contain an HTML webpage.",
            }

        content_length = response.headers.get("Content-Length")

        if content_length:
            try:
                if int(content_length) > MAX_CONTENT_LENGTH:
                    return {
                        "url": clean_url,
                        "status": "error",
                        "text": "",
                        "error": "Webpage exceeded the size limit.",
                    }
            except ValueError:
                pass

        content = bytearray()

        for chunk in response.iter_content(chunk_size=8192):
            content.extend(chunk)

            if len(content) > MAX_CONTENT_LENGTH:
                return {
                    "url": clean_url,
                    "status": "error",
                    "text": "",
                    "error": "Webpage exceeded the size limit.",
                }

        html = content.decode(
            response.encoding or "utf-8",
            errors="replace",
        )

        text = extract_page_text(html)

        if len(text.strip()) < 50:
            return {
                "url": clean_url,
                "status": "error",
                "text": "",
                "error": "No readable article content found.",
            }

        title_soup = BeautifulSoup(html, "html.parser")
        title_tag = title_soup.find("title")

        title = (
            title_tag.get_text(" ", strip=True)
            if title_tag
            else clean_url
        )

        return {
            "url": clean_url,
            "title": title[:200],
            "status": "success",
            "text": text,
        }

    except requests.Timeout:
        error = "Request timed out."

    except requests.HTTPError as exception:
        error = f"HTTP error: {exception.response.status_code}"

    except requests.RequestException:
        error = "Unable to access this webpage."

    except Exception:
        logger.exception("Unexpected webpage extraction error.")
        error = "Content extraction failed."

    return {
        "url": clean_url,
        "status": "error",
        "text": "",
        "error": error,
    }


def fetch_sources(urls):
    """Fetch multiple webpages concurrently."""

    if not isinstance(urls, list):
        return []

    unique_urls = list(dict.fromkeys(
        url for url in urls if isinstance(url, str)
    ))[:MAX_URLS]

    results = [None] * len(unique_urls)

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {
            executor.submit(fetch_single_source, url): index
            for index, url in enumerate(unique_urls)
        }

        for future in as_completed(future_map):
            index = future_map[future]

            try:
                results[index] = future.result()
            except Exception:
                results[index] = {
                    "url": unique_urls[index],
                    "status": "error",
                    "text": "",
                    "error": "Source processing failed.",
                }

    return results
