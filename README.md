# Web Crawler для скачивания текстовых страниц
**Источник данных**: Русская Википедия (ru.wikipedia.org)

## Требования

- Python 3.7+
- requests
- beautifulsoup4

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Использование

Запустите краулер:

```bash
python3 web_crawler.py
```

Краулер автоматически:
1. Соберет 100 ссылок на статьи русской Википедии
2. Скачает содержимое каждой страницы с HTML разметкой
3. Сохранит страницы в директорию `crawled_pages/`
4. Создаст файл `crawled_pages/index.txt` с индексом

Запустите tokenizer:
```bash
python3 tokenizer.py
```
Токенайзер создаст файлы с токенами и леммами, где индекс будет соответствовать файлу из crawled_pages

## Архивация результатов

Для создания архива с выкачанными страницами:

```bash
# Linux/Mac
tar -czf crawled_pages.tar.gz crawled_pages/

# Windows (PowerShell)
Compress-Archive -Path crawled_pages -DestinationPath crawled_pages.zip
```
