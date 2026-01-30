from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    username = None # username（ユーザー名）を使わず、emailをログインIDにしたいので消す。Django標準Userが持つ username 欄を 使わない宣言
    email = models.EmailField("メールアドレス", unique=True) # email をログインIDとして使う（unique=True で重複登録を禁止）
    USERNAME_FIELD = "email" # Djangoに「ログインIDはemailだよ」と教える
    REQUIRED_FIELDS = [] # createsuperuser を作るときに USERNAME_FIELD 以外で「必須として聞く項目」を指定するリスト。createsuperuser 実行時に Email と Passwordだけ聞かれる
