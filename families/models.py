# families/models.py
from django.db import models

class Family(models.Model):
    name = models.CharField("苗字", max_length=30, blank=True) # フォーム入力で空を許可,Python・画面側の話
    image_url = models.CharField("家族アイコンURL", max_length=300, blank=True)

    created_at = models.DateTimeField("作成日時", auto_now_add=True) # 作った瞬間の日時を自動保存
    updated_at = models.DateTimeField("更新日時", auto_now=True) # 更新するたびに自動更新

    def __str__(self):
        # 管理画面などで表示される文字
        return self.name or f"Family {self.id}" # nameがあればそれを表示 or まだ未設定ならFamily1のように表示