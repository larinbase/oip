import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from pathlib import Path
import time
import sys


SEED_URLS = [
    "https://ru.wikipedia.org/wiki/Заглавная_страница",
    "https://ru.wikipedia.org/wiki/Python",
    "https://ru.wikipedia.org/wiki/Программирование",
    "https://ru.wikipedia.org/wiki/Искусственный_интеллект",
    "https://ru.wikipedia.org/wiki/Машинное_обучение",
    "https://ru.wikipedia.org/wiki/Базы_данных",
    "https://ru.wikipedia.org/wiki/Алгоритм",
    "https://ru.wikipedia.org/wiki/Интернет",
    "https://ru.wikipedia.org/wiki/Операционная_система",
    "https://ru.wikipedia.org/wiki/Компьютер",
]

ALLOWED_DOMAIN = "ru.wikipedia.org"

EXCLUDED_PREFIXES = (
    "/wiki/Special:",
    "/wiki/Служебная:",
    "/wiki/Wikipedia:",
    "/wiki/Википедия:",
    "/wiki/Talk:",
    "/wiki/Обсуждение:",
    "/wiki/User:",
    "/wiki/Участник:",
    "/wiki/File:",
    "/wiki/Файл:",
    "/wiki/Template:",
    "/wiki/Шаблон:",
    "/wiki/Help:",
    "/wiki/Справка:",
    "/wiki/Category:",
    "/wiki/Категория:",
    "/wiki/Portal:",
    "/wiki/Портал:",
    "/wiki/MediaWiki:",
    "/wiki/Module:",
    "/wiki/Модуль:",
)

EXCLUDED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".pdf", ".zip", ".rar",
    ".css", ".js", ".ico", ".svg", ".mp4", ".mp3", ".avi",
    ".xml", ".json", ".woff", ".woff2", ".ttf", ".eot",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def is_valid_wiki_url(url):
    parsed = urlparse(url)

    if parsed.netloc != ALLOWED_DOMAIN:
        return False

    path = parsed.path
    if not path.startswith("/wiki/"):
        return False

    if any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False

    if any(path.lower().endswith(ext) for ext in EXCLUDED_EXTENSIONS):
        return False

    return True


def normalize_url(url):
    parsed = urlparse(url)
    return "{0}://{1}{2}".format(parsed.scheme, parsed.netloc, parsed.path)


def fetch_page(session, url):
    try:
        response = session.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return None

        if len(response.text.strip()) < 500:
            return None

        return response.text

    except requests.RequestException as e:
        print("  [ОШИБКА] {0}: {1}".format(url, e))
        return None


def extract_wiki_links(base_url, html):
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", {"id": "mw-content-text"}) or soup

    links = []
    for tag in content.find_all("a", href=True):
        href = tag["href"]
        if href.startswith("#") or href.startswith("javascript:"):
            continue

        absolute = normalize_url(urljoin(base_url, href))
        if is_valid_wiki_url(absolute):
            links.append(absolute)

    return links


def crawl(output_dir="crawled_pages", max_pages=100, delay=1.0):
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True)

    visited = set()
    queue = deque()
    index_entries = []
    downloaded = 0

    for url in [normalize_url(u) for u in SEED_URLS]:
        if is_valid_wiki_url(url):
            queue.append(url)

    print("=" * 60)
    print("  Веб-краулер — Русская Википедия")
    print("=" * 60)
    print("  Цель: {0} страниц | Задержка: {1}s".format(max_pages, delay))
    print("=" * 60)

    with requests.Session() as session:
        while queue and downloaded < max_pages:
            url = queue.popleft()

            if url in visited:
                continue

            html = fetch_page(session, url)
            if html is None:
                visited.add(url)
                continue

            visited.add(url)
            downloaded += 1

            filename = "page_{0:04d}.html".format(downloaded)
            (out_path / filename).write_text(html, encoding="utf-8")

            index_entries.append((downloaded, url))
            print("  [{0:3d}/{1}] {2}".format(downloaded, max_pages, url))

            for link in extract_wiki_links(url, html):
                if link not in visited and link not in queue:
                    queue.append(link)

            time.sleep(delay)

    index_path = out_path / "index.txt"
    with index_path.open("w", encoding="utf-8") as f:
        for num, url in index_entries:
            f.write("{0}\t{1}\n".format(num, url))

    print()
    print("=" * 60)
    print("  Готово! Скачано страниц: {0}".format(downloaded))
    print("  Директория: {0}".format(out_path.resolve()))
    print("  Индекс:     {0}".format(index_path.resolve()))
    print("=" * 60)


if __name__ == "__main__":
    try:
        import requests
        import bs4
    except ImportError:
        print("Установите зависимости: pip install requirements.txt")
        sys.exit(1)

    try:
        crawl(output_dir="crawled_pages", max_pages=100, delay=1.0)
    except KeyboardInterrupt:
        print("\n  Краулинг прерван пользователем.")
