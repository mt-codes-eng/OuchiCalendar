from django.db import models
from django.utils import timezone


class Invitation(models.Model):
    # ----------------------------------------
    # 招待URLの状態を表す選択肢
    # ----------------------------------------
    # IntegerChoices を使うと、
    # DBには数字（0, 1, 2）を保存しつつ、
    # Pythonコードではわかりやすい名前で扱える
    class Status(models.IntegerChoices):
        UNUSED = 0, "未使用"
        USED = 1, "使用済"
        EXPIRED = 2, "期限切れ"

    # ----------------------------------------
    # どの家族への招待か
    # ----------------------------------------
    # familiesアプリの Family モデルとつなぐ外部キー
    # 1つの家族に対して、複数の招待URLを作れる
    #
    # on_delete=models.CASCADE
    # → もし家族が削除されたら、その家族の招待も一緒に削除する
    #
    # related_name="invitations"
    # → Family 側から family.invitations.all() のように
    #   招待一覧を取り出せるようにする
    family = models.ForeignKey(
        "families.Family",
        on_delete=models.CASCADE,
        related_name="invitations",
    )

    # ----------------------------------------
    # 招待URLに使うトークン文字列
    # ----------------------------------------
    # 例：
    # abc123xyz... のようなランダム文字列を保存する
    #
    # unique=True
    # → 同じトークンが重複しないようにする
    invitation_token = models.CharField(max_length=300, unique=True)

    # ----------------------------------------
    # 招待URLの有効期限
    # ----------------------------------------
    # 例：
    # 作成日時 + 72時間
    expires_at = models.DateTimeField()

    # ----------------------------------------
    # 招待URLの状態
    # ----------------------------------------
    # choices=Status.choices
    # → 管理画面やフォームで選択肢として扱いやすくなる
    #
    # default=Status.UNUSED
    # → 作成直後は「未使用」にしておく
    status = models.PositiveSmallIntegerField(
        choices=Status.choices,
        default=Status.UNUSED,
    )

    # ----------------------------------------
    # 作成日時・更新日時
    # ----------------------------------------
    # auto_now_add=True
    # → レコード作成時に自動で現在日時を入れる
    #
    # auto_now=True
    # → 更新のたびに自動で現在日時に変わる
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ----------------------------------------
    # この招待URLが期限切れかどうかを判定するメソッド
    # ----------------------------------------
    # True なら期限切れ
    # False ならまだ有効期限内
    #
    # timezone.now() を使うことで、
    # Djangoのタイムゾーン設定に沿って現在時刻を取得できる
    def is_expired(self):
        return timezone.now() > self.expires_at

    # ----------------------------------------
    # 管理画面などで表示される文字
    # ----------------------------------------
    def __str__(self):
        return f"{self.family} - {self.invitation_token}"
