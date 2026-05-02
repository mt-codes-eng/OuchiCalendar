from django.db import models
from django.conf import settings
from families.models import Family
from children.models import Child

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
    
    @property
    def status_symbol(self):
        """
        ステータスの記号だけ返す
        確定 → "〇"
        調整中 → "△"
        不可 → "✕"
        """
        if self.status == self.Status.CONFIRMED:
            return "〇"
        elif self.status == self.Status.ADJUSTING:
            return "△"
        elif self.status == self.Status.IMPOSSIBLE:
            return "✕"
        # 想定外の値が入った場合は空文字
        return ""

    @property
    def display_coordination(self):
        """
        画面表示用の「対応内容」をまとめて返す
        例：
        "△送迎"
        "〇サポート"
        """
        # status_symbol（〇△✕） + 対応内容（送迎など）
        return f"{self.status_symbol}{self.get_coordination_type_display()}"


class ScheduleUserMember(models.Model):
    """
    予定メンバー（大人）を管理する中間モデル
    1つの予定に対して、複数の大人メンバーを紐づけるために使う
    """

    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name="user_memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="schedule_memberships",
    )
    created_at = models.DateTimeField( auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["schedule", "user"],
                name="unique_schedule_user_member"
            )
        ]

    def __str__(self):
        return f"{self.schedule.title} - {self.user}"


class ScheduleChildMember(models.Model):
    """
    予定メンバー（子ども）を管理する中間モデル
    1つの予定に対して、複数の子どもメンバーを紐づけるために使う
    """

    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name="child_memberships",
    )
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name="schedule_memberships",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["schedule", "child"],
                name="unique_schedule_child_member"
            )
        ]

    def __str__(self):
        return f"{self.schedule.title} - {self.child}"