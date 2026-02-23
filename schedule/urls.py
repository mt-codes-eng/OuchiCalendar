from django.urls import path
from . import views

app_name = "schedule"

urlpatterns = [
    path("", views.month_view, name="month"), # カレンダー(月表示)
    path("day/<slug:date>/", views.day_view, name="day"), # 予定・記録概要
    path("day/<slug:date>/create-choice/", views.create_choice_view, name="day_create_choice"), # 予定・記録作成選択
    path("create/", views.schedule_create_view, name="schedule_create"), # 予定作成
    path("<int:pk>/", views.schedule_detail_view, name="schedule_detail"), # 予定詳細
    path("<int:pk>/edit/", views.schedule_edit_view, name="schedule_edit"), # 予定編集
    path("<int:pk>/delete/", views.schedule_delete_view, name="schedule_delete"), # 予定削除
]