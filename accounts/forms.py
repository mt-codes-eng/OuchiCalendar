from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm # Djangoが用意してくれている「ユーザー登録用フォーム」。パスワードの確認（password1/password2）や、パスワードの安全な保存（ハッシュ化）まで面倒をみてくれる 
from django import forms

from color_assignments.constants import COLOR_HEX_MAP # 色一覧を読み込む
from color_assignments.models import FamilyColorAssignment
User = get_user_model() # AUTH_USER_MODEL で指定した User（accounts.User）を取り出す。「標準UserじゃなくてカスタムUserを使う」ために必要

class SignUpForm(UserCreationForm):
    """
    新規アカウント登録フォーム
    UserCreationForm がもともと持っている password1 / password2 を使いながら、
    表示順と表示名を整える
    """
    # 個人カラー選択欄をフォームに追加する
    # User モデルに color_code がなくても追加できる
    # ChoiceField = 選択肢の中から1つ選ぶ欄
    color_code = forms.ChoiceField(
        label="個人カラー",
        required=True,
        widget=forms.RadioSelect,
    )
    
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
        
        self.fields["color_code"].choices = [
            ("", "選択してください"),
            *[(code, COLOR_HEX_MAP[code]) for code in COLOR_HEX_MAP]
        ]
        
    def clean_color_code(self):
        """
        color_code 専用の入力チェック

        ChoiceField なので、送信される値は文字列になりやすい
        後で保存しやすいように、ここで int に変換して返す
        """
        color_code = self.cleaned_data.get("color_code")

        # 万一、未選択のまま来たらエラー
        if color_code in [None, ""]:
            raise forms.ValidationError("個人カラーを選択してください")

        try:
            color_code = int(color_code)
        except (TypeError, ValueError):
            raise forms.ValidationError("個人カラーの値が不正です")

        # 13色パレットの範囲内かチェック
        if color_code not in COLOR_HEX_MAP:
            raise forms.ValidationError("選択できない色です")

        return color_code

class UserProfileForm(forms.ModelForm):
    """
    ユーザープロフィール編集フォーム
    
    編集画面では、
    - 新しい画像を選ばなければ今の画像をそのまま使う
    - 新しい画像を選んだときだけ差し替える
    仕様にしたいので、image はフォーム上では必須にしない
    """
    # これは User モデルにはないが、画面で入力させたいのでフォームに自分で書く
    color_code = forms.ChoiceField(
        label="個人カラー",
        required=True,
    )
    
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
        
        # 個人カラーの選択肢を作る
        # choices は [(保存する値, 画面に表示する値), ...] の形
        self.fields["color_code"].choices = [
            ("", "選択してください"),
            *[(code, hex_color) for code, hex_color in COLOR_HEX_MAP.items()]
        ]
        
        # 編集対象ユーザーの現在の個人カラーを初期値として入れる
        #
        # self.instance は、フォームに渡された編集対象の User
        # 例: UserProfileForm(instance=user)
        #
        # まだ色設定がない既存ユーザーもいるので、
        # 「存在したら入れる」という安全な書き方にする
        if self.instance and self.instance.pk:
            assignment = FamilyColorAssignment.objects.filter(
                user=self.instance
            ).first()

            if assignment:
                # フォームを開いたときに、現在の色が最初から選ばれた状態にする
                self.fields["color_code"].initial = str(assignment.color_code)
       
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
    
    def clean_color_code(self):
        """
        個人カラー欄専用の入力チェック

        ChoiceField は送信時に文字列になることがあるので、
        int に変換して返す
        """
        color_code = self.cleaned_data.get("color_code")

        # 未選択チェック
        if color_code in [None, ""]:
            raise forms.ValidationError("個人カラーを選択してください")

        # 文字列 → int に変換
        try:
            color_code = int(color_code)
        except (TypeError, ValueError):
            raise forms.ValidationError("個人カラーの値が不正です")

        # 13色パレットの中にある値か確認
        if color_code not in COLOR_HEX_MAP:
            raise forms.ValidationError("選択できない色です")

        return color_code