import os
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q

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
            save_to = form.cleaned_data["save_to"]
            
            if save_to == 'db':
                url = form.cleaned_data['url']
                if PhotoMetadata.objects.filter(url=url).exists():
                    messages.error(request, "Фотография с таким URL уже есть в базе данных!")
                    return render(request, "metadata_app/add_form.html", {"form": form})
                
                form.save()
                messages.success(request, "Запись сохранена в БД.")
                
            else:
                data = {k: v for k, v in form.cleaned_data.items() if k != 'save_to'}
                if data.get('created_at'):
                    data['created_at'] = data['created_at'].isoformat()
                
                filename = save_metadata_to_file(data)
                messages.success(request, f"Запись сохранена в файл {filename}.")
                
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
    source = request.GET.get('source', 'db') 
    
    context = {'source': source}
    if source == 'db':
        context['db_items'] = PhotoMetadata.objects.all().order_by('-created')
    else:
        context['items'] = load_all_metadata_files()
        
    return render(request, "metadata_app/files_list.html", context)


def ajax_search(request):
    """Возвращает найденные записи в формате JSON для JS."""
    query = request.GET.get('q', '')
    if query:
       
        results = PhotoMetadata.objects.filter(
            Q(title__icontains=query) | 
            Q(author__icontains=query) | 
            Q(tags__icontains=query)
        ).values('id', 'title', 'author', 'format', 'width', 'height', 'size_kb', 'tags')
        return JsonResponse({'results': list(results)})
    return JsonResponse({'results': []})

def delete_metadata(request, pk):
    """Удаление записи."""
    obj = get_object_or_404(PhotoMetadata, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Запись удалена.")
        return redirect(f"{request.META.get('HTTP_REFERER', '/files/')}")
    return render(request, "metadata_app/confirm_delete.html", {"obj": obj})

def edit_metadata(request, pk):
    """Редактирование записи."""
    obj = get_object_or_404(PhotoMetadata, pk=pk)
    if request.method == "POST":
        form = PhotoMetadataForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Запись обновлена.")
            return redirect("metadata_app:files")
    else:
        
        form = PhotoMetadataForm(instance=obj)
        
    return render(request, "metadata_app/edit_form.html", {"form": form})