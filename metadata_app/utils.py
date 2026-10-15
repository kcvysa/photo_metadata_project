import json
import os
import re
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime

from django.conf import settings


UPLOAD_DIR = str(settings.UPLOAD_DIR)
ALLOWED_EXTENSIONS = {".json", ".xml"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 МБ

REQUIRED_FIELDS = {"title", "author", "url", "width", "height", "format", "size_kb"}
ALLOWED_FORMATS = {"jpeg", "png", "gif", "webp", "bmp", "tiff"}





def ensure_upload_dir() -> None:
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_metadata_to_file(data: dict, fmt: str) -> str:
    """
    Сохраняет словарь в JSON/XML. Возвращает имя созданного файла.
    """
    ensure_upload_dir()
    fmt = fmt.lower()
    if fmt not in {"json", "xml"}:
        raise ValueError("Недопустимый формат файла")

    ext = fmt
    filename = f"meta_{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)

    if fmt == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        _write_xml(path, data)

    return filename


def _write_xml(path: str, data: dict) -> None:
    root = ET.Element("photo")
    for key, value in data.items():
        child = ET.SubElement(root, key)
        if isinstance(value, list):
            for item in value:
                tag = ET.SubElement(child, "tag")
                tag.text = str(item)
        elif value is None:
            child.text = ""
        else:
            child.text = str(value)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)





_SAFE_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def sanitize_filename(name: str) -> str:
    """
    Никогда не доверяем имени от пользователя:
    берём только базовое имя, чистим символы, генерируем uuid.
    """
    base = os.path.basename(name or "")
    _, ext = os.path.splitext(base)
    ext = _SAFE_RE.sub("", ext).lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".json"
    return f"upload_{uuid.uuid4().hex}{ext}"





def validate_uploaded_file(uploaded_file):
    """
    Проверяет расширение, размер, кодировку и структуру.
    Возвращает (ok: bool, error: str | None, data: dict | None).
    """
    name = uploaded_file.name or ""
    ext = os.path.splitext(name)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return False, "Недопустимое расширение. Разрешены только .json и .xml.", None

    if uploaded_file.size > MAX_FILE_SIZE:
        return False, "Файл слишком большой (максимум 2 МБ).", None

    if uploaded_file.size == 0:
        return False, "Файл пустой.", None

    try:
        raw = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        return False, "Файл должен быть в кодировке UTF-8.", None

    try:
        if ext == ".json":
            data = json.loads(raw)
        else:
            data = _parse_xml(raw)
    except (json.JSONDecodeError, ET.ParseError) as e:
        return False, f"Ошибка разбора файла: {e}", None

    ok, error = validate_metadata(data)
    if not ok:
        return False, error, None

    return True, None, data


def _parse_xml(raw: str) -> dict:
    root = ET.fromstring(raw)
    result = {}
    for child in root:
        if len(child):
            result[child.tag] = [c.text for c in child]
        else:
            result[child.tag] = child.text
    return result


def validate_metadata(data) -> tuple[bool, str | None]:
    """Общая валидация структуры метаданных (и для файлов, и для формы)."""
    if not isinstance(data, dict):
        return False, "Корневой элемент должен быть объектом (JSON object / XML element)."

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

    # created_at — необязательное, но если есть — проверяем
    ca = data.get("created_at")
    if ca:
        try:
            datetime.fromisoformat(str(ca).replace("Z", "+00:00"))
        except ValueError:
            return False, "Поле created_at должно быть в формате ISO 8601."

    return True, None




def load_all_metadata_files() -> list:
    """
    Читает все JSON/XML файлы из UPLOAD_DIR.
    Возвращает список словарей:
        {"filename", "format", "data" | "error"}
    """
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
            if ext == ".json":
                data = json.loads(raw)
            else:
                data = _parse_xml(raw)
            result.append({"filename": name, "format": ext.lstrip("."), "data": data})
        except Exception as e:
            result.append({
                "filename": name,
                "format": ext.lstrip("."),
                "data": None,
                "error": f"Не удалось прочитать: {e}",
            })

    return result