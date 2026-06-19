from django.urls import path, include
from . import views

app_name = "families"

urlpatterns = [
    path("family-settings/", views.family_settings_view, name="family_settings"),
    path("family-profile/edit/", views.family_profile_edit_view, name="family_profile_edit"),
    path("setup-completed/finish/", views.finish_setup_completed_view, name="finish_setup_completed"),
]
