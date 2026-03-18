from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm # Djangoが用意してくれている「ユーザー登録用フォーム」。パスワードの確認（password1/password2）や、パスワードの安全な保存（ハッシュ化）まで面倒をみてくれる 
from django import forms

User = get_user_model() # AUTH_USER_MODEL で指定した User（accounts.User）を取り出す。「標準UserじゃなくてカスタムUserを使う」ために必要

class SignUpForm(UserCreationForm):
    """
    新規アカウント登録フォーム
    UserCreationForm がもともと持っている password1 / password2 を使いながら、
    表示順と表示名を整える
    """
    class Meta:
        model = User
        # パスワード2つは UserCreationForm 側が元から持っている（自分で書かなくてOK）が、
        # UserCreationForm の password1 / password2 も、ここに書くと表示順を指定できる
        fields = ("name", "email", "password1", "password2", "image") 
        labels = {
            "name": "名前",
            "email": "Email",
            "password1": "パスワード",
            "password2": "パスワード再入力",
            "image": "個人アイコン",
        }
        
        widgets = {
            # Django標準の「Currently / Clear / Change」を出さず、
            # シンプルなファイル選択欄にする
            "image": forms.FileInput(),
        }
        
    def __init__(self, *args, **kwargs):
        # フォーム生成時に、各項目の見た目や表示名を整える
        super().__init__(*args, **kwargs)

        # password1 / password2 は UserCreationForm 側が持っているフィールド
        # ここでラベルを上書きすると、画面表示をわかりやすくできる
        self.fields["password1"].label = "パスワード"
        self.fields["password2"].label = "パスワード再入力"

        # 新規登録では個人アイコンを必須にしたいので required=True にする
        # モデル側でも必須だが、フォーム側でも明示しておくとわかりやすい
        self.fields["image"].required = True

class UserProfileForm(forms.ModelForm):
    """
    ユーザープロフィール編集フォーム
    
    編集画面では、
    - 新しい画像を選ばなければ今の画像をそのまま使う
    - 新しい画像を選んだときだけ差し替える
    仕様にしたいので、image はフォーム上では必須にしない
    """
    class Meta:
        model = User
        fields = ("name", "email", "image")
        labels = {
            "name": "名前",
            "email": "Email",
            "image": "個人アイコン",
        }
        widgets = {
            # 編集画面でもシンプルなファイル選択欄にする
            "image": forms.FileInput(),
        }
    
    def __init__(self, *args, **kwargs):
        """
        フォーム生成時の初期設定
        """
        super().__init__(*args, **kwargs)

        # 編集画面では、新しい画像を選ばなくても保存できるようにしたい
        # （今の画像をそのまま使うため）
        # そのため、フォーム上では image を必須にしない
        self.fields["image"].required = False
         
    def clean_email(self):
        """
        clean_email()：email欄専用の入力チェック（追加ルール）を自分で作れる仕組み
        Djangoのフォームは form.is_valid() を呼ぶときに、
        各入力欄をチェックする
        OKなら cleaned_data に入れる
        そのとき、
        clean_フィールド名（例：clean_email）という関数があると
        Djangoが自動で呼び出す。「emailのチェックだな」と判断
        """
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