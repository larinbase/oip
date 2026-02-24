"""
tokenizer.py — Токенизация и лемматизация страниц из crawled_pages/

Для каждого page_XXXX.html создаёт:
  tokens/tokens_XXXX.txt  — уникальные токены страницы (один на строку)
  lemmas/lemmas_XXXX.txt  — леммы с токенами (лемма токен1 токен2 ...)

Требования: pip3 install -r requirements.txt
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup
import pymorphy2

CRAWLED_DIR = Path("crawled_pages")
TOKENS_DIR  = Path("tokens")
LEMMAS_DIR  = Path("lemmas")

EXCLUDED_POS = {
    "PREP",   # предлог  (в, на, под, ...)
    "CONJ",   # союз     (и, но, что, ...)
    "PRCL",   # частица  (не, бы, же, ...)
    "INTJ",   # междометие
    "NPRO",   # местоимение
}

CYRILLIC_ONLY = re.compile(r'^[а-яёА-ЯЁ]{2,}$')


# ─── Вспомогательные функции ──────────────────────────────────────────────────

def extract_text(html: str) -> str:
    """Извлекает чистый текст из HTML Wikipedia-страницы."""
    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("div", {"id": "mw-content-text"}) or soup
    for tag in body.find_all(["script", "style", "sup", "table", "math"]):
        tag.decompose()
    return body.get_text(separator=" ")


def is_valid(token: str) -> bool:
    """True, если токен состоит только из кириллицы (без цифр и мусора)."""
    return bool(CYRILLIC_ONLY.match(token))


def process_page(html: str, morph: pymorphy2.MorphAnalyzer) -> dict[str, set[str]]:
    """
    Обрабатывает одну HTML-страницу.
    Возвращает: lemma -> {token1, token2, ...}
    """
    text = extract_text(html)
    lemma_map: dict[str, set[str]] = {}

    for raw in re.findall(r'[а-яёА-ЯЁ]+', text):
        token = raw.lower()

        # Фильтр: только кириллица, минимум 2 символа
        if not is_valid(token):
            continue

        parsed = morph.parse(token)[0]

        # Фильтр: исключаем служебные части речи
        if (parsed.tag.POS or "") in EXCLUDED_POS:
            continue

        lemma = parsed.normal_form

        # Лемма тоже должна быть чистой кириллицей
        if not is_valid(lemma):
            continue

        lemma_map.setdefault(lemma, set()).add(token)

    return lemma_map


def save_page_results(stem: str, lemma_map: dict[str, set[str]]) -> None:
    """
    Сохраняет tokens/tokens_XXXX.txt и lemmas/lemmas_XXXX.txt
    для одной страницы.
    """
    # ── tokens_XXXX.txt ──────────────────────────────────────────
    all_tokens = sorted({t for tokens in lemma_map.values() for t in tokens})
    tokens_path = TOKENS_DIR / f"tokens_{stem}.txt"
    with open(tokens_path, "w", encoding="utf-8") as f:
        for token in all_tokens:
            f.write(token + "\n")

    # ── lemmas_XXXX.txt ──────────────────────────────────────────
    lemmas_path = LEMMAS_DIR / f"lemmas_{stem}.txt"
    with open(lemmas_path, "w", encoding="utf-8") as f:
        for lemma in sorted(lemma_map.keys()):
            tokens_str = " ".join(sorted(lemma_map[lemma]))
            f.write(f"{lemma} {tokens_str}\n")

    return len(all_tokens), len(lemma_map)


# ─── Основной цикл ────────────────────────────────────────────────────────────

def main() -> None:
    TOKENS_DIR.mkdir(exist_ok=True)
    LEMMAS_DIR.mkdir(exist_ok=True)

    html_files = sorted(CRAWLED_DIR.glob("page_*.html"))
    if not html_files:
        raise FileNotFoundError(
            f"Нет HTML-файлов в '{CRAWLED_DIR}'. Запустите web_crawler.py."
        )

    print(f"Найдено файлов: {len(html_files)}")
    print(f"Токены  → {TOKENS_DIR}/")
    print(f"Леммы   → {LEMMAS_DIR}/")
    print("-" * 50)

    morph = pymorphy2.MorphAnalyzer()

    for path in html_files:
        # stem = "0001" из "page_0001.html"
        stem = path.stem.split("_", 1)[1]

        html = path.read_text(encoding="utf-8")
        lemma_map = process_page(html, morph)
        n_tokens, n_lemmas = save_page_results(stem, lemma_map)

        print(f"  page_{stem}.html  →  {n_tokens:>5} токенов,  {n_lemmas:>5} лемм")

    print("-" * 50)
    print("Готово!")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"[ОШИБКА] {e}")
    except Exception as e:
        print(f"[ОШИБКА] {e}")
        raise
