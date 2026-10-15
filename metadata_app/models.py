from django.db import models


class PhotoMetadata(models.Model):
    """Метаданные о фотографии в сети."""

    FORMAT_CHOICES = [
        ("jpeg", "JPEG"),
        ("png", "PNG"),
        ("gif", "GIF"),
        ("webp", "WebP"),
        ("bmp", "BMP"),
        ("tiff", "TIFF"),
    ]

    title = models.CharField("Название", max_length=200)
    author = models.CharField("Автор", max_length=120)
    url = models.URLField("URL изображения", max_length=500)
    width = models.PositiveIntegerField("Ширина, px")
    height = models.PositiveIntegerField("Высота, px")
    format = models.CharField("Формат", max_length=10, choices=FORMAT_CHOICES)
    size_kb = models.PositiveIntegerField("Размер, KB")
    created_at = models.DateTimeField("Дата съёмки", null=True, blank=True)
    tags = models.CharField("Теги (через запятую)", max_length=300, blank=True)
    description = models.TextField("Описание", blank=True)

    # имя файла, в который была сохранена эта запись
    source_file = models.CharField("Файл-источник", max_length=120, blank=True)
    created = models.DateTimeField("Создано в системе", auto_now_add=True)

    class Meta:
        verbose_name = "Метаданные фотографии"
        verbose_name_plural = "Метаданные фотографий"
        ordering = ["-created"]

    def __str__(self):
        return self.title

    def to_dict(self) -> dict:
        """Сериализация в словарь для JSON/XML."""
        return {
            "title": self.title,
            "author": self.author,
            "url": self.url,
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "size_kb": self.size_kb,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": [t.strip() for t in self.tags.split(",") if t.strip()],
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict, source_file: str = "") -> "PhotoMetadata":
        """Создание объекта из словаря (после валидации)."""
        tags = data.get("tags") or []
        if isinstance(tags, list):
            tags = ", ".join(str(t).strip() for t in tags if str(t).strip())

        return cls(
            title=str(data["title"]).strip(),
            author=str(data["author"]).strip(),
            url=str(data["url"]).strip(),
            width=int(data["width"]),
            height=int(data["height"]),
            format=str(data["format"]).lower().strip(),
            size_kb=int(data["size_kb"]),
            created_at=data.get("created_at") or None,
            tags=tags,
            description=str(data.get("description") or "").strip(),
            source_file=source_file,
        )