from django.core.exceptions import ValidationError


class LetterAndNumberPasswordValidator:
    """
    パスワードに英字と数字の両方が含まれているか確認する
    """

    def validate(self, password, user=None):
        # 英字が1文字以上あるか
        has_letter = any(
            char.isascii() and char.isalpha()
            for char in password
        )

        # 数字が1文字以上あるか
        has_number = any(
            char.isdigit()
            for char in password
        )

        # 英字または数字のどちらかが無ければエラー
        if not has_letter or not has_number:
            raise ValidationError(
                "パスワードには英字と数字の両方を含めてください",
                code="password_requires_letter_and_number",
            )

    def get_help_text(self):
        return "パスワードには英字と数字の両方を含めてください"