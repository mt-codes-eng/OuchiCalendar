from django.urls import path
from . import views

app_name = "comments"

urlpatterns = [
    path("recent/", views.comment_recent_view, name="recent"),
]