# families/models.py
from django.db import models

class Family(models.Model):
    name = models.CharField(max_length=30) 
    image = models.ImageField(
        upload_to="families/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True) # 作った瞬間の日時を自動保存
    updated_at = models.DateTimeField(auto_now=True) # 更新するたびに自動更新

    def __str__(self):
        # 管理画面などで表示される文字
        return self.name