from django import forms
from .models import ScheduleComment

class ScheduleCommentForm(forms.ModelForm):
    """
    予定コメント投稿用フォーム

    役割
    - 宛先(to_user) を表示する
    - コメント本文(body) を表示する
    - 宛先候補を「同じ家族の大人ユーザー」に絞る
    - 初期値として担当者を入れられるようにする
    
    仕様
    - コメント入力は任意
    - コメント本文が空なら、コメントは保存しない想定
    - コメント本文が入っているときだけ、宛先を必須にする
    """

    class Meta:
        model = ScheduleComment
        # フォームに表示する項目
        fields = ["to_user", "body"]

        labels = {
            "to_user": "宛先",
            "body": "",
        }

        # body を複数行入力できる textarea にする
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 3, # 高さを3行分にする
                    "placeholder": "コメントを入力",
                }
            ),
        }

    def __init__(self, *args, schedule=None, user=None, **kwargs):
        """
        引数の意味
        -schedule:
            このコメントが紐づく予定
        -user:
            ログイン中ユーザー
        """
        super().__init__(*args, **kwargs)
        
        # コメントは任意入力にする
        self.fields["body"].required = False
        # 宛先も、本文が空なら未選択でよいので任意
        self.fields["to_user"].required = False
        
        # まずは宛先候補を空にしておく
        # （万一 schedule も user も渡らなかったときに全ユーザーが出るのを防ぐ）
        self.fields["to_user"].queryset = self.fields["to_user"].queryset.none()

        # ① schedule が渡されている場合
        #    → その予定の family に所属するユーザーだけ宛先候補にする
        if schedule and schedule.family_id:
            family_users = schedule.family.user_set.all()
            self.fields["to_user"].queryset = family_users

            # 担当者が設定されていれば、宛先の初期値にする
            if schedule.user_id:
                self.fields["to_user"].initial = schedule.user

        # ② まだ schedule から family が取れない場合
        #    → ログイン中ユーザーの family に所属するユーザーを候補にする
        elif user and getattr(user, "family_id", None):
            family_users = user.family.user_set.all()
            self.fields["to_user"].queryset = family_users

    def clean_body(self):
        """
        コメント本文(body) の個別バリデーション
        """
        body = self.cleaned_data.get("body", "")

        # 未入力なら空文字のまま返す
        # 今回はコメント任意なので、ここではエラーにしない
        if not body:
            return ""

        # 前後の空白を削除する
        body = body.strip()

        # 空白だけ入力された場合も、空文字として扱う
        if body == "":
            return ""

        # 文字数上限チェック
        if len(body) > 300:
            raise forms.ValidationError("コメントは300文字以内で入力してください")

        return body

    def clean(self):
        """
        フォーム全体のバリデーション

        ここでは
        - コメント本文が入っているのに宛先が未選択
        をチェックする
        """
        cleaned_data = super().clean()

        body = cleaned_data.get("body")
        to_user = cleaned_data.get("to_user")

        # コメント本文があるのに宛先が未選択ならエラー
        if body and not to_user:
            self.add_error("to_user", "宛先を選択してください")

        return cleaned_data