from django.urls import path # このファイルの中で path という関数を使えるようにする宣言
from . import views # 同じアプリの views.py を読む

app_name = 'pages'
urlpatterns = [
    path("", views.portfolio, name="portfolio"), # 「もしURLが ""（トップページ）だったらviews.py の中にある portfolio という関数を実行」
]