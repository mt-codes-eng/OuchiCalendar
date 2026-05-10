# records/urls.py
from django.urls import path
from . import views

app_name = "records"

urlpatterns = [
    path("create/", views.record_create_view, name="create"), # 記録作成
    path("bowel/<int:pk>/", views.bowel_record_detail_view, name="bowel_detail"), # 排便記録詳細
    path("absence/<int:pk>/", views.absence_record_detail_view, name="absence_detail"), # 欠席記録詳細
    path("bowel/<int:pk>/edit/", views.bowel_record_edit_view, name="bowel_edit"), # 排便記録編集
    path("absence/<int:pk>/edit/", views.absence_record_edit_view, name="absence_edit"), # 欠席記録編集
]