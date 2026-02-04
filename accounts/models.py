# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # username（ユーザー名）を使わず、emailをログインIDにしたいので消す。Django標準Userが持つ username 欄を使わない宣言
    username = None 
    
    # email をログインIDとして使う（unique=True で重複登録を禁止）
    email = models.EmailField(
        verbose_name="メールアドレス",
        unique=True,
    ) 
    
    family = models.ForeignKey(
        "families.Family", # 文字列参照。参照先（アプリ名.モデル名）= familiesアプリのFamilyモデルを参照。
        on_delete=models.PROTECT, # CASCADE:親（Family）を消したら子（User）も一緒に消えるだと困る
        null=True, # DBでNULL許可
        blank=True, # フォーム入力で空を許可
        related_name="users", # 逆参照名
        verbose_name="家族", # 表示名
    )
    
    name = models.CharField(
        verbose_name="名前",
        max_length=30,
        blank=True,
    )
    
    image_url = models.CharField(
        verbose_name="ユーザーアイコン",
        max_length=300,
        blank=True,
    )

    # 作成日時は AbstractUser の date_joined を使う
    # 更新日時
    updated_at = models.DateTimeField(
       verbose_name= "更新日時",
        auto_now=True,
    )
    
    # Djangoに「ログインIDはemailだよ」と教える
    USERNAME_FIELD = "email"
    # createsuperuser を作るときに USERNAME_FIELD 以外で「必須として聞く項目」を指定するリスト。createsuperuser 実行時に Email と Passwordだけ聞かれる 
    REQUIRED_FIELDS = [] 
    
    def __str__(self):
        return self.name or self.email