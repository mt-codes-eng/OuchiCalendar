# children/models.py
from django.db import models

class Child(models.Model):
    family = models.ForeignKey(
        "families.Family",
        verbose_name="家族",
        on_delete=models.CASCADE,
        related_name="children",
    )
    name = models.CharField(verbose_name="子ども名", max_length=30)
    image_url = models.CharField(verbose_name="子どもアイコン", max_length=300, blank=True)
    
    created_at = models.DateTimeField(verbose_name="作成日時", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新日時", auto_now=True)
    
    def __str__(self):
        return self.name