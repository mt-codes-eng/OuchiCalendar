from django.shortcuts import render, redirect
from .forms import SignUpForm
from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # 本人確認を実行して結果を返す
        user = authenticate(request, email=email, password=password)

        if user is not None:
            # その結果が成功かどうかを見る
            # 認証成功
            # 成功した人だけログイン状態にする（「この人はログイン済みです」をサーバ側で覚える）。
            # requestとログインユーザで関数を呼び出すとログインが完了し、セッション内にログインユーザーの情報を格納する。
            login(request, user)

            # 次に行きたいページがあればそこへ、なければスケジュールへ。
            # 「ログイン画面に来るとき、元々行きたかったURLがあればそれを取り出す。あればそこへ行かせる。なければ、決め打ちのスケジュール画面へ行かせる。」
            next_url = request.GET.get("next")
            return redirect(next_url or "/ouchi-calendar/schedule/")

        
        else:
            # 認証失敗（メール or パスワード違い）
            return render(
            request,
            "accounts/login.html",
            {"error": "メールアドレスまたはパスワードが違います"}
        )

    return render(request, "accounts/login.html")



def signup_view(request):
    if request.method == "POST":
        # 送信されたデータ（記入済みの紙）でフォームを作る
        form = SignUpForm(request.POST)

        # 入力チェック（メール形式、パスワード一致、強度など）
        if form.is_valid():
            form.save()  # ユーザー作成（パスワードは安全にハッシュ化されて保存される）
            return redirect("accounts:login")  # いったんログイン画面へ

    else:
        # GETのときは空のフォーム（空白の紙）
        form = SignUpForm() # その型から作られた実物（インスタンス）。何も書かれていない入力用の紙を1枚用意した

    # Python的に省略していない形はreturn render(request=request,template_name="accounts/signup.html",context={"form": form})
    # {"form": form}でその紙をHTMLに渡して、『accounts/signup.htmlに表示して』と頼んだ。テンプレート側で form を使えるように。辞書の意味：左 "form" → HTMLで使う名前、右 form → Pythonで作った申込書そのもの。
    return render(request, "accounts/signup.html", {"form": form}) 
    