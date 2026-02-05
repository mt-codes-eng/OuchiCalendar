from django.urls import path
from . import views

app_name = "families"

urlpatterns = [
    path("settings/", views.family_settings_view, name="settings"),
]
