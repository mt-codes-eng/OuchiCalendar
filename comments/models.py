from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from schedule.models import Schedule

class ScheduleComment(models.Model):
    """
    予定に紐づくコメントモデル
    """

    # コメント種別
    # 0 = ユーザーが投稿した通常コメント
    # 1 = システムが自動で入れる通知コメント
    COMMENT_TYPE_USER = 0
    COMMENT_TYPE_SYSTEM = 1

    COMMENT_TYPE_CHOICES = [
        (COMMENT_TYPE_USER, "ユーザーコメント"),
        (COMMENT_TYPE_SYSTEM, "システム通知"),
    ]

    # どの予定に対するコメントか
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name="comments",
    ) 

    # コメント投稿者
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_schedule_comments",
    )

    # コメントの宛先
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_schedule_comments",
    )

    # コメント種別
    comment_type = models.IntegerField(
        choices=COMMENT_TYPE_CHOICES,
        default=COMMENT_TYPE_USER,
    )

    # コメント本文
    # TextField は長めの文章向き
    # blank=False にしたいので、空欄投稿は不可
    body = models.TextField()

    # 作成日時
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # 更新日時
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        # 管理画面などでの表示順
        # 古い順に並べると会話の流れを追いやすい
        ordering = ["created_at"]

    def __str__(self):
        """
        管理画面や shell で見たときに分かりやすい表示にする
        """
        return f"{self.schedule.title} / {self.from_user} → {self.to_user}"

    def clean(self):
        """
        モデル全体のバリデーション

        ここでは「関連オブジェクトが入ったあとにだけ確認したい業務ルール」をチェックする
        """
        errors = {}

        # schedule が入っているときだけ、
        # 「対応・調整が必要な予定だけコメント可能」をチェックする
        if self.schedule_id and not self.schedule.requires_coordination:
            errors["schedule"] = "対応・調整が必要な予定だけコメントできます"

        if errors:
            raise ValidationError(errors)
