from django.urls import path

from . import views


app_name = "metadata_app"

urlpatterns = [
    path("", views.index, name="index"),
    path("add/", views.add_metadata, name="add"),
    path("upload/", views.upload_file, name="upload"),
    path("files/", views.files_list, name="files"),

    path("edit/<int:pk>/", views.edit_metadata, name="edit"),
    path("delete/<int:pk>/", views.delete_metadata, name="delete"),
    path("ajax/search/", views.ajax_search, name="ajax_search"),
]