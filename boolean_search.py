"""
boolean_search.py — Булев поиск по инвертированному индексу

Поддерживаемые операторы:
    AND  — пересечение
    OR   — объединение
    NOT  — отрицание (документы, НЕ содержащие термин)
    ()   — группировка для сложных запросов

Примеры запросов:
    клеопатра
    (клеопатра AND цезарь) OR (антоний AND цицерон) OR помпей
    NOT война AND история
"""

import json
import re
import sys
from pathlib import Path

import pymorphy2

INDEX_FILE = Path("inverted_index.json")
_morph = pymorphy2.MorphAnalyzer()


def load_index(path: Path) -> dict:
    """Загружает инвертированный индекс из JSON, значения — множества doc_id."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {lemma: set(docs) for lemma, docs in raw.items()}

def lemmatize(word: str) -> str:
    """Возвращает начальную форму слова (лемму) через pymorphy2."""
    return _morph.parse(word.lower())[0].normal_form

_QUERY_RE = re.compile(
    r'\(|\)|AND\b|OR\b|NOT\b|[а-яёА-ЯЁa-zA-Z][а-яёА-ЯЁa-zA-Z]*',
    re.IGNORECASE,
)

def tokenize_query(query: str) -> list:
    """Разбивает строку запроса на токены: операторы, скобки, термины."""
    result = []
    for t in _QUERY_RE.findall(query):
        result.append(t.upper() if t.upper() in ("AND", "OR", "NOT") else t)
    return result

class BooleanQueryParser:
    def __init__(self, tokens: list, index: dict, all_docs: set):
        self.tokens = tokens
        self.pos = 0
        self.index = index
        self.all_docs = all_docs

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected=None):
        token = self.tokens[self.pos]
        if expected and token != expected:
            raise SyntaxError(f"Ожидалось '{expected}', получено '{token}'")
        self.pos += 1
        return token

    def parse(self) -> set:
        result = self.parse_or()
        if self.pos < len(self.tokens):
            raise SyntaxError(f"Неожиданный токен: '{self.peek()}'")
        return result

    def parse_or(self) -> set:
        left = self.parse_and()
        while self.peek() == "OR":
            self.consume("OR")
            right = self.parse_and()
            left = left | right
        return left

    def parse_and(self) -> set:
        left = self.parse_not()
        while self.peek() == "AND":
            self.consume("AND")
            right = self.parse_not()
            left = left & right
        return left

    def parse_not(self) -> set:
        if self.peek() == "NOT":
            self.consume("NOT")
            operand = self.parse_primary()
            return self.all_docs - operand
        return self.parse_primary()

    def parse_primary(self) -> set:
        token = self.peek()
        if token == "(":
            self.consume("(")
            result = self.parse_or()
            self.consume(")")
            return result
        if token is None:
            raise SyntaxError("Неожиданный конец запроса")
        if token in ("AND", "OR", "NOT", ")"):
            raise SyntaxError(f"Неожиданный оператор: '{token}'")
        self.pos += 1
        lemma = lemmatize(token)
        return self.index.get(lemma, set())


def boolean_search(query: str, index: dict, all_docs: set) -> set:
    """Выполняет булев поиск по индексу и возвращает множество doc_id."""
    tokens = tokenize_query(query)
    if not tokens:
        return set()
    return BooleanQueryParser(tokens, index, all_docs).parse()

def load_page_index(path: Path = Path("crawled_pages/index.txt")) -> dict:
    """Загружает соответствие doc_id -> URL из index.txt краулера."""
    page_index = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t", 1)
                if len(parts) == 2:
                    try:
                        page_index[int(parts[0])] = parts[1]
                    except ValueError:
                        pass
    return page_index


def main():
    if not INDEX_FILE.exists():
        print(f"[ОШИБКА] Файл индекса не найден: {INDEX_FILE}")
        print("Сначала запустите: python inverted_index.py")
        sys.exit(1)

    print("Загрузка инвертированного индекса...")
    index = load_index(INDEX_FILE)
    all_docs = set().union(*index.values()) if index else set()
    page_index = load_page_index()

    print(f"Индекс загружен: {len(index)} лемм, {len(all_docs)} документов")
    print("=" * 60)
    print(" Булев поиск. Операторы: AND  OR  NOT  ( )")
    print(" Пример: (клеопатра AND цезарь) OR помпей")
    print(" Введите 'выход' для завершения.")
    print("=" * 60)

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

        try:
            results = boolean_search(query, index, all_docs)
            sorted_results = sorted(results)

            if not sorted_results:
                print("  Ничего не найдено.")
            else:
                print(f"  Найдено документов: {len(sorted_results)}")
                for doc_id in sorted_results:
                    url = page_index.get(doc_id, f"page_{doc_id:04d}.html")
                    print(f"    [{doc_id:3d}] {url}")

        except SyntaxError as e:
            print(f"  [СИНТАКСИЧЕСКАЯ ОШИБКА] {e}")
        except Exception as e:
            print(f"  [ОШИБКА] {e}")


if __name__ == "__main__":
    main()
