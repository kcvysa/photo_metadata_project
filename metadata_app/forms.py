from django import forms

from .models import PhotoMetadata


class PhotoMetadataForm(forms.ModelForm):

    class Meta:
        model = PhotoMetadata
        fields = [
            "title", "author", "url", "width", "height",
            "format", "size_kb", "created_at", "tags", "description",
        ]
        widgets = {
            "created_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["created_at"].input_formats = ["%Y-%m-%dT%H:%M"]

        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 2:
            raise forms.ValidationError("Название должно содержать минимум 2 символа.")
        return title

    def clean_author(self):
        author = self.cleaned_data["author"].strip()
        if len(author) < 2:
            raise forms.ValidationError("Имя автора слишком короткое.")
        return author

    def clean_url(self):
        url = self.cleaned_data["url"].strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            raise forms.ValidationError("URL должен начинаться с http:// или https://")
        return url

    def clean_width(self):
        w = self.cleaned_data["width"]
        if w < 1 or w > 100_000:
            raise forms.ValidationError("Ширина должна быть в диапазоне 1–100000 px.")
        return w

    def clean_height(self):
        h = self.cleaned_data["height"]
        if h < 1 or h > 100_000:
            raise forms.ValidationError("Высота должна быть в диапазоне 1–100000 px.")
        return h

    def clean_size_kb(self):
        size = self.cleaned_data["size_kb"]
        if size < 1 or size > 1_000_000:
            raise forms.ValidationError("Размер должен быть в диапазоне 1–1 000 000 KB.")
        return size

    def clean_tags(self):
        tags = self.cleaned_data.get("tags", "") or ""
        parts = [t.strip() for t in tags.split(",") if t.strip()]
        if len(parts) > 20:
            raise forms.ValidationError("Не более 20 тегов.")
        for p in parts:
            if len(p) > 50:
                raise forms.ValidationError("Каждый тег не длиннее 50 символов.")
        return ", ".join(parts)

    def clean(self):
        cleaned = super().clean()
        w, h = cleaned.get("width"), cleaned.get("height")
        if w and h and w * h > 100_000_000:
            raise forms.ValidationError(
                "Слишком большое разрешение (> 100 Мпикс)."
            )
        return cleaned


class UploadFileForm(forms.Form):
    file = forms.FileField(
        label="Файл метаданных (.json)",
        widget=forms.ClearableFileInput(
            attrs={"accept": ".json", "class": "form-control"}
        ),
    )