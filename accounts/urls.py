from django.urls import path 
from . import views 

app_name = "accounts"
urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("password/change", views.password_change_view, name="password_change"), 
]