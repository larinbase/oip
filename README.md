# Web Crawler для скачивания текстовых страниц
**Источник данных**: Русская Википедия (ru.wikipedia.org)

## Требования

- Python 3.7+
- requests
- beautifulsoup4
- pymorphy2
- pymorphy2-dicts-ru


## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Использование

### 1) Запустите краулер:

```bash
python3 web_crawler.py
```

Краулер автоматически:
1. Соберет 100 ссылок на статьи русской Википедии
2. Скачает содержимое каждой страницы с HTML разметкой
3. Сохранит страницы в директорию `crawled_pages/`
4. Создаст файл `crawled_pages/index.txt` с индексом

### 2) Запустите tokenizer:
```bash
python3 tokenizer.py
```
Токенайзер создаст файлы с токенами и леммами, где индекс будет соответствовать файлу из crawled_pages

### 3) Создайте inverted index:
```bash
python3 inverted_index.py
```
Инвертированный индекс создаст файлы с обратным индексом, где ключ - слово, значение - список файлов, в которых встречается это слово.

Чтобы протестировать поиск, используйте команду: 
```bash 
python3 boolean_search.py
``` 
и введите поисковый запрос в терминале, следуя инструкциям после запуска в консоли.

### 4) Вычислите TF-IDF:
```bash
python3 tfidf.py
```
TF-IDF вычисляет важность слов в документах.


## Архивация результатов

Для создания архива с выкачанными страницами:

```bash
# Linux/Mac
tar -czf crawled_pages.tar.gz crawled_pages/

# Windows (PowerShell)
Compress-Archive -Path crawled_pages -DestinationPath crawled_pages.zip
```
