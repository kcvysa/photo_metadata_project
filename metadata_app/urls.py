from django.urls import path

from . import views


app_name = "metadata_app"

urlpatterns = [
    path("", views.index, name="index"),
    path("add/", views.add_metadata, name="add"),
    path("upload/", views.upload_file, name="upload"),
    path("files/", views.files_list, name="files"),
]