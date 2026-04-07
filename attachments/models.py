# attachments/models.py
from django.db import models

class ScheduleAttachment(models.Model):
    """
    予定に紐づく添付ファイルを管理するモデル

    1つの予定に対して、
    複数の添付ファイルを保存できるようにする
    """

    # どの予定に紐づく添付ファイルかを表す
    # scheduleアプリのScheduleモデルを参照している
    schedule = models.ForeignKey(
        'schedule.Schedule',
        on_delete=models.CASCADE,
        related_name='attachments',
    )

    # 実際のファイル本体を保存するフィールド
    # upload_to='schedule_attachments/' にすると、
    # media/schedule_attachments/ 配下に保存される
    file = models.FileField(
        upload_to='schedule_attachments/'
    )

    # 元のファイル名を保存する欄
    # 表示用・検索用に使いやすいように別で持っておく
    file_name = models.CharField(
        max_length=300,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        管理画面などで表示される文字列
        """
        return self.file_name or self.file.name

    @property
    def is_image(self):
        """
        この添付ファイルが画像かどうかを判定する
        テンプレートで使いやすくするため @property をつけている
        - 計算して返す値を、項目みたいに使えるようにする便利機能
        - 例えば def name(self):
                    eturn "田中"
          という関数が sample.name() ではなく sample.nameで呼び出せるようになる
        """
        # ファイルがあるか確認
        if not self.file:
            return False

        # lower()：ファイル名を小文字にする関数
        # endswith()：〜で終わるかチェックする関数
        # 拡張子で種類判定。ファイル名が、これらの拡張子で終わっているか
        return self.file.name.lower().endswith(
            ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        )

    @property
    def is_pdf(self):
        """
        この添付ファイルがPDFかどうかを判定する
        """
        if not self.file:
            return False

        # ファイル名が .pdf で終わるか
        return self.file.name.lower().endswith('.pdf')