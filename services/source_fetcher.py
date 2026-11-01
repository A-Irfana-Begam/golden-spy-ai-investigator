
import requests
import socket
import ipaddress

from bs4 import BeautifulSoup
from urllib.parse import urlparse


MAX_CONTENT_SIZE = 1_000_000
MAX_TEXT_LENGTH = 20000

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GoldenSpy/1.0)"
}


def validate_url(url):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")

    if not parsed.hostname:
        raise ValueError("Invalid hostname.")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed.")

    if parsed.port and parsed.port not in (80, 443):
        raise ValueError("Only standard HTTP and HTTPS ports are allowed.")

    host = parsed.hostname

    try:
        addresses = socket.getaddrinfo(
            host,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM
        )
    except socket.gaierror:
        raise ValueError("Unable to resolve website hostname.")

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if not ip.is_global:
            raise ValueError("Private or restricted IP addresses are not allowed.")

    return parsed


def extract_content(html, url):
    soup = BeautifulSoup(html, "html.parser")

    title = (
        soup.title.get_text(" ", strip=True)
        if soup.title else url
    )

    for tag in soup([
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "noscript",
        "svg",
        "iframe",
        "form"
    ]):
        tag.decompose()

    content = soup.find("main") or soup.find("article") or soup.body or soup

    text = " ".join(content.stripped_strings)

    return title, text[:MAX_TEXT_LENGTH]


def fetch_sources(urls):
    results = []

    for url in urls:
        try:
            parsed = validate_url(url)

            with requests.get(
                url,
                headers=HEADERS,
                timeout=(5, 15),
                allow_redirects=False,
                stream=True
            ) as response:

                if 300 <= response.status_code < 400:
                    raise ValueError("Website redirects are not supported. Use its final URL.")

                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type", ""
                ).lower()

                if (
                    "text/html" not in content_type
                    and "application/xhtml+xml" not in content_type
                ):
                    raise ValueError("URL does not contain an HTML webpage.")

                content_length = response.headers.get("Content-Length")

                if content_length and int(content_length) > MAX_CONTENT_SIZE:
                    raise ValueError("Webpage is too large to process.")

                chunks = []
                total_size = 0

                for chunk in response.iter_content(8192):
                    if not chunk:
                        continue

                    total_size += len(chunk)

                    if total_size > MAX_CONTENT_SIZE:
                        raise ValueError("Webpage exceeded the 1 MB size limit.")

                    chunks.append(chunk)

                response.encoding = response.encoding or "utf-8"
                html = b"".join(chunks).decode(
                    response.encoding,
                    errors="replace"
                )

            title, text = extract_content(html, url)

            if not text.strip():
                raise ValueError("No readable webpage content found.")

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
