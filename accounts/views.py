from django.shortcuts import render
from .forms import SignUpForm

def login_view(request):
    return render(request, "accounts/login.html")

def signup_view(request):
    form = SignUpForm() # その型から作られた実物（インスタンス）。まだ何も書かれていない入力用の紙を1枚用意した
    # {"form": form}でその紙をHTMLに渡して、『ここに表示してね』と頼んだ。テンプレート側で form を使えるように。辞書の意味：左 "form" → HTMLで使う名前、右 form → Pythonで作った申込書そのもの。
    return render(request, "accounts/signup.html", {"form": form}) # Python的に省略していない形はreturn render(request=request,template_name="accounts/signup.html",context={"form": form})