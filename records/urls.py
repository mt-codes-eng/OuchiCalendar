# records/urls.py
from django.urls import path
from . import views

app_name = "records"

urlpatterns = [
    path("create/", views.record_create_view, name="create"), # 記録作成画面
]