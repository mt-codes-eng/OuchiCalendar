from django.urls import path
from . import views

app_name = "children"

urlpatterns = [
    path("create/", views.child_create_view, name="child_create"), # 追加 
    path("<int:pk>/edit/", views.child_edit_view, name="child_edit"), # 編集
    path("<int:pk>/delete/", views.child_delete_view, name="child_delete"), # 削除
]