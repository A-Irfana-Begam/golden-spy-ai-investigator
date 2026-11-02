
import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs, unquote

import requests
from bs4 import BeautifulSoup


MAX_SOURCES = 8
MAX_CONTENT_SIZE = 500_000
MAX_TEXT_LENGTH = 6000
MAX_WORKERS = 4

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GoldenSpy/1.0)"
}

SEARCH_TIMEOUT = (5, 10)
FETCH_TIMEOUT = (5, 12)


def validate_url(url):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Invalid URL.")

    parsed = urlparse(url.strip())

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")

    if not parsed.hostname:
        raise ValueError("Invalid hostname.")

    if parsed.username or parsed.password:
        raise ValueError("URL credentials are not allowed.")

    try:
        port = parsed.port
    except ValueError:
        raise ValueError("Invalid URL port.")

    if port and port not in (80, 443):
        raise ValueError("Only standard HTTP/HTTPS ports are allowed.")

    hostname = parsed.hostname.rstrip(".").lower()

    try:
        addresses = socket.getaddrinfo(
            hostname,
            port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM
        )
    except socket.gaierror:
        raise ValueError("Unable to resolve website hostname.")

    if not addresses:
        raise ValueError("Unable to resolve website hostname.")

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if not ip.is_global:
            raise ValueError("Private IP addresses are not allowed.")

    return parsed


def discover_sources(question, limit=5):
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
            timeout=SEARCH_TIMEOUT
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.select("a.result__a"):
            href = link.get("href", "").strip()

            if not href:
                continue

            parsed_link = urlparse(href)
            query = parse_qs(parsed_link.query)

            if "uddg" in query:
                href = unquote(query["uddg"][0])

            try:
                parsed = validate_url(href)

                if parsed.hostname.lower().endswith("duckduckgo.com"):
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


def fetch_one_source(url):
    result = {
        "url": url,
        "title": url,
        "status": "error",
        "text": "",
        "error": ""
    }

    try:
        parsed = validate_url(url)

        with requests.get(
            url,
            headers=HEADERS,
            timeout=FETCH_TIMEOUT,
            allow_redirects=False,
            stream=True
        ) as response:

            if 300 <= response.status_code < 400:
                raise ValueError(
                    "Redirect detected. Use the final webpage URL."
                )

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type", ""
            ).lower()

            if not any(value in content_type for value in (
                "text/html",
                "application/xhtml+xml"
            )):
                raise ValueError("URL is not an HTML webpage.")

            content_length = response.headers.get("Content-Length")

            if content_length:
                try:
                    if int(content_length) > MAX_CONTENT_SIZE:
                        raise ValueError("Webpage is too large.")
                except ValueError as error:
                    if str(error) == "Webpage is too large.":
                        raise
                    raise ValueError("Invalid webpage size.")

            chunks = []
            total_size = 0

            for chunk in response.iter_content(8192):
                if not chunk:
                    continue

                total_size += len(chunk)

                if total_size > MAX_CONTENT_SIZE:
                    raise ValueError("Webpage exceeded the size limit.")

                chunks.append(chunk)

            html = b"".join(chunks).decode(
                response.encoding or "utf-8",
                errors="replace"
            )

        title, text = extract_content(html, url)

        if not text.strip():
            raise ValueError("No readable webpage content found.")

        result.update({
            "title": title,
            "status": "success",
            "text": text,
            "error": ""
        })

    except Exception as error:
        result["error"] = str(error)

    return result


def fetch_sources(urls):
    if not isinstance(urls, list):
        return []

    unique_urls = list(dict.fromkeys(
        url.strip()
        for url in urls[:MAX_SOURCES]
        if isinstance(url, str) and url.strip()
    ))

    results = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_one_source, url): index
            for index, url in enumerate(unique_urls)
        }

        for future in as_completed(futures):
            index = futures[future]

            try:
                results[index] = future.result()
            except Exception as error:
                results[index] = {
                    "url": unique_urls[index],
                    "title": unique_urls[index],
                    "status": "error",
                    "text": "",
                    "error": str(error)
                }

    return [
        results[index]
        for index in range(len(unique_urls))
    ]
