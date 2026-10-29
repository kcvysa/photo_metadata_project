import os

from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import PhotoMetadataForm, UploadFileForm
from .models import PhotoMetadata
from .utils import (
    UPLOAD_DIR,
    ensure_upload_dir,
    load_all_metadata_files,
    sanitize_filename,
    save_metadata_to_file,
    validate_metadata,
    validate_uploaded_file,
)


def index(request):
    return render(request, "metadata_app/index.html")


def add_metadata(request):
    if request.method == "POST":
        form = PhotoMetadataForm(request.POST)

        if form.is_valid():
            obj = form.save()
            data = obj.to_dict()
            ok, error = validate_metadata(data)
            
            if not ok:
                obj.delete()
                messages.error(request, f"Ошибка валидации перед сохранением: {error}")
                return redirect("metadata_app:add")

            try:
                filename = save_metadata_to_file(data)
            except OSError as e:
                obj.delete()
                messages.error(request, f"Не удалось сохранить файл: {e}")
                return redirect("metadata_app:add")

            obj.source_file = filename
            obj.save(update_fields=["source_file"])

            messages.success(
                request,
                f"Запись сохранена в БД и в файл {filename}.",
            )
            return redirect("metadata_app:add")
    else:
        form = PhotoMetadataForm()

    return render(request, "metadata_app/add_form.html", {"form": form})


def upload_file(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = request.FILES["file"]
            ok, error, data = validate_uploaded_file(uploaded)

            if not ok:
                messages.danger(request, f"Файл отклонён и удалён: {error}")
                return redirect("metadata_app:upload")

            ensure_upload_dir()
            safe_name = sanitize_filename(uploaded.name)
            path = os.path.join(UPLOAD_DIR, safe_name)

            try:
                with open(path, "wb+") as dest:
                    for chunk in uploaded.chunks():
                        dest.write(chunk)
            except OSError as e:
                messages.danger(request, f"Не удалось сохранить файл: {e}")
                return redirect("metadata_app:upload")

            try:
                obj = PhotoMetadata.from_dict(data, source_file=safe_name)
                obj.full_clean(exclude=["created_at", "created", "source_file"])
                obj.save()
            except Exception as e:
                messages.warning(
                    request,
                    f"Файл сохранён как {safe_name}, но запись в БД не создана: {e}",
                )
                return redirect("metadata_app:files")

            messages.success(
                request,
                f"Файл загружен как {safe_name} и запись добавлена в БД.",
            )
            return redirect("metadata_app:files")
    else:
        form = UploadFileForm()

    return render(request, "metadata_app/upload.html", {"form": form})


def files_list(request):
    items = load_all_metadata_files()
    db_items = PhotoMetadata.objects.all()
    return render(
        request,
        "metadata_app/files_list.html",
        {
            "items": items,
            "has_files": bool(items),
            "db_items": db_items,
            "has_db": db_items.exists(),
        },
    )