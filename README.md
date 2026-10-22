# Photo Metadata (Django)

Веб-приложение на Django для работы с метаданными о фотографиях в сети.
Поддерживает импорт/экспорт в форматах **JSON**, сохраняет данные
в файлы и дублирует записи в базу данных.

## Возможности

- Ввод метаданных о фотографии через HTML-форму.
- Валидация вводимых данных.
- Сохранение записи одновременно в файл `.json` и в базу данных.
- Загрузка файлов `.json` на сервер с полной проверкой (размер, UTF-8, структура).
- Невалидный файл не сохраняется.
- Имя файла генерируется автоматически (UUID).
- Просмотр всех JSON-файлов и записей из БД.
- Bootstrap 5 для оформления.

## Стек

- Python 3.10+
- Django 5.x
- SQLite (встроенная БД)
- XML — стандартная библиотека `xml.etree.ElementTree`
- JSON — стандартная библиотека `json`

## Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/<твой-логин>/photo_metadata_project.git
cd photo_metadata_project

# 2. Создать и активировать виртуальное окружение
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Применить миграции
python manage.py migrate

# 5. Запустить сервер разработки
python manage.py runserver