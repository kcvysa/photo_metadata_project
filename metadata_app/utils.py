import json
import os
import re
import uuid
from datetime import datetime

from django.conf import settings


UPLOAD_DIR = str(settings.UPLOAD_DIR)
ALLOWED_EXTENSIONS = {".json"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 МБ

REQUIRED_FIELDS = {"title", "author", "url", "width", "height", "format", "size_kb"}
ALLOWED_FORMATS = {"jpeg", "png", "gif", "webp", "bmp", "tiff"}


def ensure_upload_dir() -> None:
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_metadata_to_file(data: dict) -> str:
    """Сохраняет словарь в JSON. Возвращает имя созданного файла."""
    ensure_upload_dir()
    filename = f"meta_{uuid.uuid4().hex}.json"
    path = os.path.join(UPLOAD_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filename


_SAFE_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def sanitize_filename(name: str) -> str:
    base = os.path.basename(name or "")
    _, ext = os.path.splitext(base)
    ext = _SAFE_RE.sub("", ext).lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".json"
    return f"upload_{uuid.uuid4().hex}{ext}"


def validate_uploaded_file(uploaded_file):
    name = uploaded_file.name or ""
    ext = os.path.splitext(name)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return False, "Недопустимое расширение. Разрешены только .json.", None

    if uploaded_file.size > MAX_FILE_SIZE:
        return False, "Файл слишком большой (максимум 2 МБ).", None

    if uploaded_file.size == 0:
        return False, "Файл пустой.", None

    try:
        raw = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        return False, "Файл должен быть в кодировке UTF-8.", None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return False, f"Ошибка разбора файла: {e}", None

    ok, error = validate_metadata(data)
    if not ok:
        return False, error, None

    return True, None, data


def validate_metadata(data) -> tuple[bool, str | None]:
    if not isinstance(data, dict):
        return False, "Корневой элемент должен быть объектом JSON."

    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        return False, f"Отсутствуют обязательные поля: {', '.join(sorted(missing))}."

    try:
        w = int(data["width"])
        h = int(data["height"])
        size = int(data["size_kb"])
    except (TypeError, ValueError):
        return False, "Поля width, height, size_kb должны быть целыми числами."

    if not (1 <= w <= 100_000) or not (1 <= h <= 100_000):
        return False, "Ширина/высота должны быть в диапазоне 1–100000 px."

    if not (1 <= size <= 1_000_000):
        return False, "Размер должен быть в диапазоне 1–1 000 000 KB."

    fmt = str(data["format"]).lower().strip()
    if fmt not in ALLOWED_FORMATS:
        return False, f"Недопустимый формат изображения: {fmt}."

    url = str(data["url"]).strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "URL должен начинаться с http:// или https://"

    for key in ("title", "author"):
        if not str(data[key]).strip():
            return False, f"Поле {key} не может быть пустым."

    ca = data.get("created_at")
    if ca:
        try:
            datetime.fromisoformat(str(ca).replace("Z", "+00:00"))
        except ValueError:
            return False, "Поле created_at должно быть в формате ISO 8601."

    return True, None


def load_all_metadata_files() -> list:
    if not os.path.isdir(UPLOAD_DIR):
        return []

    result = []
    for name in sorted(os.listdir(UPLOAD_DIR)):
        path = os.path.join(UPLOAD_DIR, name)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
            result.append({"filename": name, "format": "json", "data": data})
        except Exception as e:
            result.append({
                "filename": name,
                "format": "json",
                "data": None,
                "error": f"Не удалось прочитать: {e}",
            })

    return result