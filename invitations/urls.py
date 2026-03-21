from django.urls import path
from . import views

app_name = "invitations"

urlpatterns = [
    path("create/", views.invitation_create_view, name="create"),
    path("accept/<str:token>/", views.invitation_accept_view, name="accept"),
    path("invalid/", views.invitation_invalid_view, name="invalid"),
]