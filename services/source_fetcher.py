import requests
from bs4 import BeautifulSoup

def fetch_sources(urls):
    fetched = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else url
            text = " ".join(soup.stripped_strings)

            fetched.append({
                "url": url,
                "title": title,
                "status": "success",
                "text": text
            })
        except Exception as e:
            fetched.append({
                "url": url,
                "title": url,
                "status": "error",
                "error": str(e)
            })

    return fetched