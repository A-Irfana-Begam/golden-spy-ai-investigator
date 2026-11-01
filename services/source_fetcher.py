
import requests
import socket
import ipaddress

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, parse_qs, unquote


MAX_CONTENT_SIZE = 1_000_000
MAX_TEXT_LENGTH = 20000
MAX_SOURCES = 8

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GoldenSpy/1.0)"
}


def validate_url(url):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Invalid URL.")

    parsed = urlparse(url.strip())

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")

    if not parsed.hostname:
        raise ValueError("Invalid hostname.")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed.")

    try:
        port = parsed.port
    except ValueError:
        raise ValueError("Invalid URL port.")

    if port and port not in (80, 443):
        raise ValueError("Only standard HTTP and HTTPS ports are allowed.")

    hostname = parsed.hostname.rstrip(".")

    try:
        ip = ipaddress.ip_address(hostname)

        if not ip.is_global:
            raise ValueError("Private or restricted IP addresses are not allowed.")

    except ValueError as error:
        if "Private or restricted" in str(error):
            raise

        try:
            addresses = socket.getaddrinfo(
                hostname,
                port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM
            )
        except socket.gaierror:
            raise ValueError("Unable to resolve website hostname.")

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])

            if not ip.is_global:
                raise ValueError(
                    "Private or restricted IP addresses are not allowed."
                )

    return parsed


def discover_sources(question, limit=5):
    """Discover webpages using DuckDuckGo HTML search."""

    if not isinstance(question, str) or not question.strip():
        return []

    if not isinstance(limit, int) or limit <= 0:
        return []

    limit = min(limit, MAX_SOURCES)

    search_url = "https://html.duckduckgo.com/html/"
    discovered = []
    seen = set()

    try:
        response = requests.get(
            search_url,
            params={"q": question.strip()},
            headers=HEADERS,
            timeout=(5, 12)
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.select("a.result__a"):
            href = link.get("href", "").strip()

            if not href:
                continue

            if "uddg=" in href:
                parsed_link = urlparse(href)

                href = parse_qs(
                    parsed_link.query
                ).get("uddg", [""])[0]

                href = unquote(href)

            href = urljoin(search_url, href)

            try:
                parsed = validate_url(href)

                if parsed.hostname in (
                    "html.duckduckgo.com",
                    "duckduckgo.com",
                    "www.duckduckgo.com"
                ):
                    continue

                normalized = parsed._replace(
                    fragment=""
                ).geturl()

                if normalized in seen:
                    continue

                seen.add(normalized)
                discovered.append(normalized)

                if len(discovered) >= limit:
                    break

            except (ValueError, TypeError):
                continue

    except requests.RequestException:
        return []

    except Exception:
        return []

    return discovered[:limit]


def extract_content(html, url):
    soup = BeautifulSoup(html, "html.parser")

    title = (
        soup.title.get_text(" ", strip=True)
        if soup.title else url
    )

    for tag in soup([
        "script", "style", "nav", "footer", "header",
        "noscript", "svg", "iframe", "form"
    ]):
        tag.decompose()

    content = (
        soup.find("main")
        or soup.find("article")
        or soup.body
        or soup
    )

    text = " ".join(content.stripped_strings)

    return title, text[:MAX_TEXT_LENGTH]


def fetch_sources(urls):
    results = []
    seen = set()

    if not isinstance(urls, list):
        return results

    for url in urls[:MAX_SOURCES]:
        if not isinstance(url, str):
            continue

        url = url.strip()

        if not url or url in seen:
            continue

        seen.add(url)

        try:
            validate_url(url)

            with requests.get(
                url,
                headers=HEADERS,
                timeout=(5, 15),
                allow_redirects=False,
                stream=True
            ) as response:

                if 300 <= response.status_code < 400:
                    raise ValueError(
                        "Website redirect detected. "
                        "Use the final webpage URL."
                    )

                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type", ""
                ).lower()

                if (
                    "text/html" not in content_type
                    and "application/xhtml+xml" not in content_type
                ):
                    raise ValueError(
                        "URL is not an HTML webpage."
                    )

                content_length = response.headers.get(
                    "Content-Length"
                )

                if content_length:
                    try:
                        if int(content_length) > MAX_CONTENT_SIZE:
                            raise ValueError("Webpage is too large.")
                    except ValueError:
                        raise ValueError(
                            "Invalid or excessive webpage size."
                        )

                chunks = []
                total_size = 0

                for chunk in response.iter_content(8192):
                    if not chunk:
                        continue

                    total_size += len(chunk)

                    if total_size > MAX_CONTENT_SIZE:
                        raise ValueError(
                            "Webpage exceeded the 1 MB limit."
                        )

                    chunks.append(chunk)

                html = b"".join(chunks).decode(
                    response.encoding or "utf-8",
                    errors="replace"
                )

            title, text = extract_content(html, url)

            if not text.strip():
                raise ValueError(
                    "No readable webpage content found."
                )

            results.append({
                "url": url,
                "title": title,
                "status": "success",
                "text": text
            })

        except Exception as error:
            results.append({
                "url": url,
                "title": url,
                "status": "error",
                "error": str(error)
            })

    return results
