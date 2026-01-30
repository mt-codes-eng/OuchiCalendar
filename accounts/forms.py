from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm # Djangoが用意してくれている「ユーザー登録用フォーム」。パスワードの確認（password1/password2）や、パスワードの安全な保存（ハッシュ化）まで面倒をみてくれる 

User = get_user_model() # AUTH_USER_MODEL で指定した User（accounts.User）を取り出す。「標準UserじゃなくてカスタムUserを使う」ために必要

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email",) # 登録フォームに「email」を出す指定。パスワード2つは UserCreationForm 側が元から持っている（自分で書かなくてOK）