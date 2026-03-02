"""
vector_search.py — Поисковая система на основе векторного TF-IDF поиска

Алгоритм:
    1. Загружаем TF-IDF векторы документов из tfidf_lemmas/
    2. Для запроса строим TF-IDF вектор (используем IDF из корпуса)
    3. Вычисляем косинусное сходство запроса с каждым документом
    4. Возвращаем топ-N результатов по убыванию схожести

Зависит от: tfidf.py (задание 4), tokenizer.py (задание 2)
"""

import re
import math
import sys
from pathlib import Path
from collections import Counter

import pymorphy2

TFIDF_LEMMAS_DIR = Path("tfidf_lemmas")
PAGE_INDEX_FILE  = Path("crawled_pages/index.txt")

CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]{2,}')
_morph      = pymorphy2.MorphAnalyzer()


def lemmatize(word: str) -> str:
    """Приводит слово к начальной форме (лемме)."""
    return _morph.parse(word.lower())[0].normal_form

class SearchEngine:
    """
    Векторная поисковая система на основе TF-IDF.

    Атрибуты:
        doc_vectors  — { doc_id: { лемма: tf-idf } }
        idf          — { лемма: idf }  (из корпуса, нужен для вектора запроса)
        doc_norms    — { doc_id: ||вектор|| }  (предвычислено для скорости)
        page_index   — { doc_id: url }
    """

    def __init__(self):
        self.doc_vectors: dict = {}
        self.idf:         dict = {}
        self.doc_norms:   dict = {}
        self.page_index:  dict = {}
        self._load_index()

    def _load_index(self) -> None:
        tfidf_files = sorted(TFIDF_LEMMAS_DIR.glob("tfidf_*.txt"))
        if not tfidf_files:
            raise FileNotFoundError(
                f"Файлы TF-IDF не найдены в '{TFIDF_LEMMAS_DIR}'."
                " Сначала запустите tfidf.py."
            )

        print(f"Загрузка TF-IDF из {len(tfidf_files)} документов...")

        for path in tfidf_files:
            stem   = path.stem.split("_", 1)[1]
            doc_id = int(stem)
            vector = {}

            with open(path, encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 3:
                        lemma       = parts[0]
                        idf_val     = float(parts[1])
                        tfidf_val   = float(parts[2])
                        vector[lemma] = tfidf_val

                        if lemma not in self.idf:
                            self.idf[lemma] = idf_val

            self.doc_vectors[doc_id] = vector

            self.doc_norms[doc_id] = math.sqrt(
                sum(v * v for v in vector.values())
            )

        if PAGE_INDEX_FILE.exists():
            with open(PAGE_INDEX_FILE, encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("\t", 1)
                    if len(parts) == 2:
                        try:
                            self.page_index[int(parts[0])] = parts[1]
                        except ValueError:
                            pass

        print(
            f"Индекс загружен: {len(self.doc_vectors)} документов, "
            f"{len(self.idf)} уникальных лемм"
        )

    def _build_query_vector(self, query: str) -> dict:
        """
        Строит TF-IDF вектор для запроса.

        TF(лемма, запрос)  = count(лемма, запрос) / |запрос|
        IDF(лемма)         = берём из корпуса (незнакомые леммы игнорируются)
        """
        raw_tokens = CYRILLIC_RE.findall(query)
        if not raw_tokens:
            return {}

        lemmas = [lemmatize(t) for t in raw_tokens]
        counts = Counter(lemmas)
        total  = len(lemmas)

        return {
            lemma: (count / total) * self.idf[lemma]
            for lemma, count in counts.items()
            if lemma in self.idf
        }

    @staticmethod
    def _cosine(q_vec: dict, d_vec: dict, d_norm: float) -> float:
        """
        cos(q, d) = (q · d) / (||q|| * ||d||)
        Скалярное произведение считаем только по пересечению векторов.
        """
        if not d_norm:
            return 0.0

        dot    = sum(q_vec.get(lemma, 0.0) * tfidf for lemma, tfidf in d_vec.items())
        q_norm = math.sqrt(sum(v * v for v in q_vec.values()))

        if not q_norm:
            return 0.0

        return dot / (q_norm * d_norm)

    def search(self, query: str, top_n: int = 10) -> list:
        """
        Векторный поиск по запросу.

        Возвращает:
            [ { doc_id, url, score }, ... ]  — отсортированы по убыванию score
        """
        q_vec = self._build_query_vector(query)
        if not q_vec:
            return []

        scores = [
            (doc_id, self._cosine(q_vec, d_vec, self.doc_norms[doc_id]))
            for doc_id, d_vec in self.doc_vectors.items()
        ]

        scores = sorted(
            ((doc_id, s) for doc_id, s in scores if s > 0.0),
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]

        return [
            {
                "doc_id": doc_id,
                "url":    self.page_index.get(doc_id, f"page_{doc_id:04d}.html"),
                "score":  round(score, 6),
            }
            for doc_id, score in scores
        ]

def main():
    print("=" * 65)
    print("  Векторный поиск  |  TF-IDF + косинусное сходство")
    print("=" * 65)

    try:
        engine = SearchEngine()
    except FileNotFoundError as e:
        print(f"[ОШИБКА] {e}")
        sys.exit(1)

    print()
    print("  Введите запрос на русском языке.")
    print("  Введите 'выход' для завершения.")
    print("=" * 65)

    while True:
        try:
            query = input("\nЗапрос> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nЗавершение.")
            break

        if not query:
            continue
        if query.lower() in ("выход", "exit", "quit"):
            print("До свидания!")
            break

        results = engine.search(query, top_n=10)

        if not results:
            print("  Ничего не найдено.")
        else:
            print(f"\n  Топ-{len(results)} результатов по запросу: \"{query}\"")
            print(f"  {'─' * 62}")
            print(f"  {'#':<4} {'Сходство':>10}  URL")
            print(f"  {'─' * 62}")
            for i, r in enumerate(results, 1):
                print(f"  {i:<4} {r['score']:>10.6f}  {r['url']}")
            print(f"  {'─' * 62}")


if __name__ == "__main__":
    main()
