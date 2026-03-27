# color_assignments/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from .constants import COLOR_HEX_MAP # 画面表示用の色コード辞書を読み込む

class FamilyColorAssignment(models.Model):
    """
    家族内の色設定を管理するモデル

    1レコード = 1つの色割り当て

    例
    - 合同予定カラー
    - 大人メンバーの個人カラー
    - 子どもメンバーの個人カラー
    """

    class AssignType(models.IntegerChoices):
        SHARED = 0, "合同"
        USER = 1, "大人"
        CHILD = 2, "子ども"

    class ColorCode(models.IntegerChoices):
        # DBには 0〜12 の数字を保存する
        # 右側の文字は「表示名」
        COLOR_0 = 0, "0: #ff7f7f"
        COLOR_1 = 1, "1: #ff7fbf"
        COLOR_2 = 2, "2: #ffbcff"
        COLOR_3 = 3, "3: #bf7fff"
        COLOR_4 = 4, "4: #7f7fff"
        COLOR_5 = 5, "5: #7fbfff"
        COLOR_6 = 6, "6: #7fffff"
        COLOR_7 = 7, "7: #99ffcc"
        COLOR_8 = 8, "8: #7fff7f"
        COLOR_9 = 9, "9: #bfff7f"
        COLOR_10 = 10, "10: #ffff7f"
        COLOR_11 = 11, "11: #ffbf7f"
        COLOR_12 = 12, "12: #c2bbb2"

    # どの家族の色設定か
    family = models.ForeignKey(
        "families.Family",
        on_delete=models.CASCADE,
        related_name="color_assignments",
    )

    # 大人メンバーの個人カラーのときだけ入る
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="color_assignments",
    )

    # 子どもメンバーの個人カラーのときだけ入る
    child = models.ForeignKey(
        "children.Child",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="color_assignments",
    )

    # 13色パレットのどれを使うか
    color_code = models.IntegerField(
        choices=ColorCode.choices,
    )

    # 合同 / 大人 / 子ども のどれか
    assign_type = models.IntegerField(
        choices=AssignType.choices,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # 同じ家族内では同じ色を重複して使えない
            models.UniqueConstraint(
                fields=["family", "color_code"],
                name="unique_family_color_code",
            ),

            # 1人の大人メンバーに対して、個人カラー設定は1件まで(userごとに1レコードしか持てない)
            # condition=models.Q(...)：条件付きユニーク制約
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(user__isnull=False), # user があるときだけ user の重複禁止
                name="unique_color_assignment_per_user",
            ),

            # 1人の子どもメンバーに対して、個人カラー設定は1件まで
            models.UniqueConstraint(
                fields=["child"],
                condition=models.Q(child__isnull=False), # child があるときだけ child の重複禁止
                name="unique_color_assignment_per_child",
            ),

            # 1家族に対して、合同予定カラーは1件まで
            models.UniqueConstraint(
                fields=["family", "assign_type"],
                condition=models.Q(assign_type=0), # assign_type=SHARED のときだけ familyごと1件
                name="unique_shared_color_per_family",
            ),
        ]

    def clean(self):
        """
        モデル全体の整合性チェック

        これは主に
        - 開発中に変なデータを防ぐ
        - DBにおかしな組み合わせを入れない
        ためのチェック

        ユーザー向けのやさしいエラー表示は、
        後でフォーム側でも行う
        """

        # 合同予定カラーのとき
        if self.assign_type == self.AssignType.SHARED:
            # 合同予定カラーには user も child も入れない
            if self.user is not None:
                raise ValidationError("合同予定カラーの設定では user は保存できません。")
            if self.child is not None:
                raise ValidationError("合同予定カラーの設定では child は保存できません。")

        # 大人メンバーの個人カラーのとき
        elif self.assign_type == self.AssignType.USER:
            # user は必須
            if self.user is None:
                raise ValidationError("大人メンバーの個人カラーには user が必要です。")

            # child は入れてはいけない
            if self.child is not None:
                raise ValidationError("大人メンバーの個人カラーには child は保存できません。")

            # user が所属する家族と、この色設定の family が一致しているか確認
            if self.user.family_id != self.family_id:
                raise ValidationError("user の家族と color assignment の family が一致していません。")

        # 子どもメンバーの個人カラーのとき
        elif self.assign_type == self.AssignType.CHILD:
            # child は必須
            if self.child is None:
                raise ValidationError("子どもメンバーの個人カラーには child が必要です。")

            # user は入れてはいけない
            if self.user is not None:
                raise ValidationError("子どもメンバーの個人カラーには user は保存できません。")

            # child が所属する家族と、この色設定の family が一致しているか確認
            if self.child.family_id != self.family_id:
                raise ValidationError("child の家族と color assignment の family が一致していません。")

    def get_hex_color(self):
        """
        color_code から実際のHEXカラーを返す

        例:
        color_code = 3 → "#bf7fff"
        """
        return COLOR_HEX_MAP[self.color_code]

    def __str__(self):
        return f"{self.family} / {self.get_assign_type_display()} / {self.get_color_code_display()}"