from django.db import models
from children.models import Child

class BowelMovementRecord(models.Model):
    """
    排便記録モデル
    子ども1人につき、1日1件だけ排便記録を作れる
    """
    # 記録対象の子ども
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name="bowel_movement_records",
    )

    # 記録日
    record_date = models.DateField()

    # 排便があったか
    has_bowel_movement = models.BooleanField(default=False)

    # 排便メモ
    memo = models.TextField(blank=True)

    # 気になることがあるか
    has_concern = models.BooleanField(default=False)

    # 気になることのメモ
    concern_memo = models.TextField(blank=True)

    # 作成日時
    created_at = models.DateTimeField(auto_now_add=True)

    # 更新日時
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # 同じ子ども・同じ日付の記録を重複登録できない(1人の子どもにつき、1日1件だけ排便記録を登録できる)
        constraints = [
            models.UniqueConstraint(
                fields=["child", "record_date"],
                name="unique_bowel_movement_record_per_child_per_date",
            )
        ]
        ordering = ["-record_date", "-created_at"]

    def __str__(self):
        return f"{self.child} / {self.record_date} / 排便記録"


class AbsenceRecord(models.Model):
    """
    欠席記録モデル
    子ども1人につき、1日1件だけ欠席記録を作れる
    """
    # 記録対象の子ども
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name="absence_records",
    )

    # 記録日
    record_date = models.DateField()

    # 欠席したか
    is_absent = models.BooleanField(default=False)

    # 欠席メモ
    memo = models.TextField(blank=True)

    # 作成日時
    created_at = models.DateTimeField(auto_now_add=True)

    # 更新日時
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # 同じ子ども・同じ日付の記録を重複登録できない(1人の子どもにつき、1日1件だけ排便記録を登録できる)
        constraints = [
            models.UniqueConstraint(
                fields=["child", "record_date"],
                name="unique_absence_record_per_child_per_date",
            )
        ]
        ordering = ["-record_date", "-created_at"]

    def __str__(self):
        return f"{self.child} / {self.record_date} / 欠席記録"