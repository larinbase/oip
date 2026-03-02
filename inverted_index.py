"""
inverted_index.py — Построение инвертированного индекса из файлов лемм

Читает lemmas/lemmas_XXXX.txt и строит словарь:
    лемма -> отсортированный список номеров документов

Сохраняет результат в inverted_index.json
"""

import json
from pathlib import Path
from collections import defaultdict

LEMMAS_DIR = Path("lemmas")
OUTPUT_FILE = Path("inverted_index.json")


def build_inverted_index(lemmas_dir: Path) -> dict:
    """Строит инвертированный индекс из всех файлов лемм."""
    index = defaultdict(set)

    lemma_files = sorted(lemmas_dir.glob("lemmas_*.txt"))
    if not lemma_files:
        raise FileNotFoundError(
            f"Нет файлов лемм в '{lemmas_dir}'. Запустите tokenizer.py."
        )

    print(f"Найдено файлов с леммами: {len(lemma_files)}")

    for path in lemma_files:
        stem = path.stem.split("_", 1)[1]
        doc_id = int(stem)

        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                lemma = line.split()[0]
                index[lemma].add(doc_id)

    result = {lemma: sorted(docs) for lemma, docs in sorted(index.items())}
    return result


def save_index(index: dict, output_file: Path) -> None:
    """Сохраняет индекс в JSON файл."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"Инвертированный индекс сохранён: {output_file}")
    print(f"Всего лемм в индексе: {len(index)}")


def main():
    index = build_inverted_index(LEMMAS_DIR)
    save_index(index, OUTPUT_FILE)
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
