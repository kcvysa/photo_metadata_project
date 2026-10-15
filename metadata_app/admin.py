from django.contrib import admin
from .models import PhotoMetadata


@admin.register(PhotoMetadata)
class PhotoMetadataAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "format", "width", "height", "size_kb", "created")
    list_filter = ("format",)
    search_fields = ("title", "author", "tags")