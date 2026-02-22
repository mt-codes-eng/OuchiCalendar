from django.db import models
from django.conf import settings
from families.models import Family

class Schedule(models.Model):
    class CoordinationType(models.IntegerChoices):
        ABSENCE_SUPPORT = 0, "欠席対応"
        CARE = 1, "ケア(体調)"
        PICKUP = 2, "送迎"
        SUPPORT = 3, "サポート"
        OTHER = 4, "その他"
        
    class Status(models.IntegerChoices):
        CONFIRMED = 0, "〇 確定(了承済)"
        ADJUSTING = 1, "△ 調整中(返事待ち)"
        IMPOSSIBLE = 2, "✕ 不可"
        
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE, 
        related_name="schedules",
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_schedules",
    )
    
    title = models.CharField(max_length=100)
    memo = models.CharField(max_length=300, blank=True)
    
    is_all_day = models.BooleanField(default=False)
    
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    
    requires_coordination = models.BooleanField(default=False)
    
    coordination_type = models.PositiveSmallIntegerField(
        choices=CoordinationType.choices, # Django が用意してくれている「選択肢リスト」。中身は[(0, "欠席対応"), (1, "ケア(体調)"), (2, "送迎"), (3, "サポート"), (4, "その他")]というイメージ
        null=True,
        blank=True,
    )
    
    coordination_other_detail = models.CharField(max_length=100, blank=True)
    
    status = models.PositiveSmallIntegerField(
        choices=Status.choices,
        null=True,
        blank=True,
    )
    
    is_consecutive_coordination = models.BooleanField(default=False)
    coordination_end_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title