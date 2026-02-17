from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm # Djangoが用意してくれている「ユーザー登録用フォーム」。パスワードの確認（password1/password2）や、パスワードの安全な保存（ハッシュ化）まで面倒をみてくれる 
from django import forms

User = get_user_model() # AUTH_USER_MODEL で指定した User（accounts.User）を取り出す。「標準UserじゃなくてカスタムUserを使う」ために必要

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("name", "email") # 登録フォームに「name」「email」を出す指定。パスワード2つは UserCreationForm 側が元から持っている（自分で書かなくてOK）
        

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("name", "email", "image_url")
    
    """
    clean_email()：email欄専用の入力チェック（追加ルール）を自分で作れる仕組み
    Djangoのフォームは form.is_valid() を呼ぶときに、
    各入力欄をチェックする
    OKなら cleaned_data に入れる
    そのとき、
    clean_フィールド名（例：clean_email）という関数があると
    Djangoが自動で呼び出す。「emailのチェックだな」と判断
    """
         
    def clean_email(self):
        # 辞書cleaned_dataのemailキーを使って値を取り出す。cleaned_dataはビューのform.is_valid() が呼ばれたときに作られる
        email = self.cleaned_data["email"]
        # User.objects.filter(email=email)：入力されたemailを使っているユーザーを探す
        # self.instance.pk：ビューでUserProfileForm(instance=user)としているため、編集対象のユーザー（ログイン中の自分）のID
        # qs：QuerySet。検索結果をqsという変数に代入
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            # フォームにエラーを出して、保存を止める
            raise forms.ValidationError("このメールアドレスはすでに使用されています")
        return email