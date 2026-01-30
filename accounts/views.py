from django.shortcuts import render, redirect
from .forms import SignUpForm

def login_view(request):
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
    