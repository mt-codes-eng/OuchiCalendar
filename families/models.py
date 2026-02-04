# families/models.py
from django.db import models

class Family(models.Model):
    name = models.CharField(verbose_name="家族名", max_length=30, blank=True) # フォーム入力で空を許可,Python・画面側の話
    image_url = models.CharField(verbose_name="家族アイコン", max_length=300, blank=True)

    created_at = models.DateTimeField(verbose_name="作成日時", auto_now_add=True) # 作った瞬間の日時を自動保存
    updated_at = models.DateTimeField(verbose_name="更新日時", auto_now=True) # 更新するたびに自動更新

    def __str__(self):
        # 管理画面などで表示される文字
        return self.name or f"Family {self.id}" # nameがあればそれを表示 or まだ未設定ならFamily1のように表示