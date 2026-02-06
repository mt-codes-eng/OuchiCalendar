from django.urls import path
from . import views

app_name = "families"

urlpatterns = [
    path("family-settings/", views.family_settings_view, name="family_settings"),
]
