from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("logout/", views.logout_view, name="logout"),
    path("howto/", views.howto_view, name="howto"), 
]
