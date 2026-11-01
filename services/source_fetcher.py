import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import ipaddress
import socket


def fetch_sources(urls):
    results = []

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for url in urls:
        try:
            parsed = urlparse(url)

            if parsed.scheme not in ("http", "https"):
                raise ValueError("Invalid URL scheme")

            host = parsed.hostname

            if not host:
                raise ValueError("Invalid hostname")

            addresses = socket.getaddrinfo(host, None)

            for address in addresses:
                ip = ipaddress.ip_address(address[4][0])
                if not ip.is_global:
                    raise ValueError("Private addresses are not allowed")

            response = requests.get(
                url,
                headers=headers,
                timeout=10,
                allow_redirects=False
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup([
                "script", "style", "nav",
                "footer", "header", "noscript"
            ]):
                tag.decompose()

            title = (
                soup.title.get_text(strip=True)
                if soup.title else url
            )

            text = " ".join(soup.stripped_strings)

            results.append({
                "url": url,
                "title": title,
                "status": "success",
                "text": text[:20000]
            })

        except Exception as error:
            results.append({
                "url": url,
                "title": url,
                "status": "error",
                "error": str(error)
            })

    return results
