"""
tfidf.py — Подсчёт TF-IDF для токенов и лемм

Входные данные (из заданий 1 и 2):
    crawled_pages/page_XXXX.html  — скачанные страницы
    lemmas/lemmas_XXXX.txt        — леммы и их токены

Выходные данные:
    tfidf_tokens/tfidf_XXXX.txt   — <токен> <idf> <tf-idf>
    tfidf_lemmas/tfidf_XXXX.txt   — <лемма> <idf> <tf-idf>

Формулы:
    TF(token, doc)  = count(token, doc) / total_tokens(doc)
    TF(lemma, doc)  = sum(count(t, doc) for t in lemma_tokens) / total_tokens(doc)
    IDF(term)       = log(N / df(term))          # натуральный логарифм
    TF-IDF          = TF * IDF
"""

import re
import math
from pathlib import Path
from collections import defaultdict, Counter
from bs4 import BeautifulSoup

CRAWLED_DIR   = Path("crawled_pages")
LEMMAS_DIR    = Path("lemmas")
OUT_TOKENS    = Path("tfidf_tokens")
OUT_LEMMAS    = Path("tfidf_lemmas")

CYRILLIC_RE   = re.compile(r'[а-яёА-ЯЁ]{2,}')

def extract_tokens(html: str) -> list:
    """Извлекает все кириллические токены (с повторами) из HTML."""
    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("div", {"id": "mw-content-text"}) or soup
    for tag in body.find_all(["script", "style", "sup", "table", "math"]):
        tag.decompose()
    text = body.get_text(separator=" ")
    return [t.lower() for t in CYRILLIC_RE.findall(text)]


def load_lemma_map(path: Path) -> dict:
    """
    Читает lemmas_XXXX.txt и возвращает:
        { лемма: {токен1, токен2, ...} }
    """
    lemma_map = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 1:
                lemma_map[parts[0]] = set(parts[1:])
    return lemma_map

def collect_all_data():
    html_files = sorted(CRAWLED_DIR.glob("page_*.html"))
    if not html_files:
        raise FileNotFoundError(
            f"Нет HTML-файлов в '{CRAWLED_DIR}'. Запустите web_crawler.py."
        )

    N = len(html_files)
    print(f"Документов: {N}")

    # doc_id -> Counter токенов
    docs_token_counts: dict = {}
    # doc_id -> { лемма: set токенов }
    docs_lemma_maps: dict = {}

    for path in html_files:
        stem    = path.stem.split("_", 1)[1]   # "0001"
        doc_id  = int(stem)

        html    = path.read_text(encoding="utf-8")
        tokens  = extract_tokens(html)
        docs_token_counts[doc_id] = Counter(tokens)

        lemma_path = LEMMAS_DIR / f"lemmas_{stem}.txt"
        if lemma_path.exists():
            docs_lemma_maps[doc_id] = load_lemma_map(lemma_path)
        else:
            docs_lemma_maps[doc_id] = {}

    return N, docs_token_counts, docs_lemma_maps


def compute_df(N, docs_token_counts, docs_lemma_maps):
    # DF токенов: сколько документов содержат данный токен
    token_df: dict = defaultdict(int)
    for counts in docs_token_counts.values():
        for token in counts:
            token_df[token] += 1

    # DF лемм: сколько документов содержат данную лемму
    lemma_df: dict = defaultdict(int)
    for doc_id, lemma_map in docs_lemma_maps.items():
        counts = docs_token_counts[doc_id]
        for lemma, lemma_tokens in lemma_map.items():
            if any(counts.get(t, 0) > 0 for t in lemma_tokens):
                lemma_df[lemma] += 1

    return token_df, lemma_df


def save_results(N, docs_token_counts, docs_lemma_maps, token_df, lemma_df):
    OUT_TOKENS.mkdir(exist_ok=True)
    OUT_LEMMAS.mkdir(exist_ok=True)

    for path in sorted(CRAWLED_DIR.glob("page_*.html")):
        stem   = path.stem.split("_", 1)[1]
        doc_id = int(stem)

        counts     = docs_token_counts[doc_id]
        total_toks = sum(counts.values())
        if total_toks == 0:
            continue

        lemma_map  = docs_lemma_maps[doc_id]

        token_out = OUT_TOKENS / f"tfidf_{stem}.txt"
        with open(token_out, "w", encoding="utf-8") as f:
            for token in sorted(counts.keys()):
                tf    = counts[token] / total_toks
                df    = token_df.get(token, 1)
                idf   = math.log(N / df)
                tfidf = tf * idf
                f.write(f"{token} {idf:.6f} {tfidf:.6f}\n")

        lemma_out = OUT_LEMMAS / f"tfidf_{stem}.txt"
        with open(lemma_out, "w", encoding="utf-8") as f:
            for lemma in sorted(lemma_map.keys()):
                lemma_tokens = lemma_map[lemma]
                # TF леммы = сумма вхождений всех её токенов / всего токенов
                lemma_count = sum(counts.get(t, 0) for t in lemma_tokens)
                if lemma_count == 0:
                    continue
                tf    = lemma_count / total_toks
                df    = lemma_df.get(lemma, 1)
                idf   = math.log(N / df)
                tfidf = tf * idf
                f.write(f"{lemma} {idf:.6f} {tfidf:.6f}\n")

        print(f"  page_{stem}.html → {len(counts)} токенов, {len(lemma_map)} лемм")


def main():
    print("=" * 60)
    print(" TF-IDF вычисление")
    print("=" * 60)

    N, docs_token_counts, docs_lemma_maps = collect_all_data()

    print("Вычисление DF...")
    token_df, lemma_df = compute_df(N, docs_token_counts, docs_lemma_maps)
    print(f"  Уникальных токенов в корпусе : {len(token_df)}")
    print(f"  Уникальных лемм в корпусе    : {len(lemma_df)}")
    print("-" * 60)

    print("Сохранение файлов...")
    save_results(N, docs_token_counts, docs_lemma_maps, token_df, lemma_df)

    print("-" * 60)
    print(f"Готово!")
    print(f"  Токены → {OUT_TOKENS}/")
    print(f"  Леммы  → {OUT_LEMMAS}/")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"[ОШИБКА] {e}")
    except Exception as e:
        print(f"[ОШИБКА] {e}")
        raise
