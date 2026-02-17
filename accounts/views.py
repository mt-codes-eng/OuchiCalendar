from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate, login, update_session_auth_hash
from .forms import SignUpForm, UserProfileForm
from families.models import Family

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # 本人確認を実行して結果を返す
        user = authenticate(request, username=email, password=password)

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
            # ① Userを作るけどまだDBには保存しない（familyを入れてから保存したい）
            user = form.save(commit=False)
            
            # ② 1人目用：DBにFamilyレコードを1件作る。空のFamilyを作成（家族名はあとで設定画面で入れる）
            family = Family.objects.create(name="")
            
            # ③ 紐づけ（さっき作ったfamilyを、Userのfamily欄に入れる）
            user.family = family
            
            # ④ User保存（パスワードはUserCreationFormがハッシュ化してくれる）
            user.save()
            
            # ⑤ そのままログイン状態にする
            login(request, user)
             
            # ⑥ 家族設定画面へ遷移
            return redirect("families:family_settings") 

    else:
        # GETのときは空のフォーム（空白の紙）
        form = SignUpForm() # その型から作られた実物（インスタンス）。何も書かれていない入力用の紙を1枚用意した

    # Python的に省略していない形はreturn render(request=request,template_name="accounts/signup.html",context={"form": form})
    # {"form": form}でその紙をHTMLに渡して、『accounts/signup.htmlに表示して』と頼んだ。テンプレート側で form を使えるように。辞書の意味：左 "form" → HTMLで使う名前、右 form → Pythonで作った申込書そのもの。
    return render(request, "accounts/signup.html", {"form": form}) 
    
@login_required
def password_change_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # update_session_auth_hash：パスワード変更後に、今のログイン状態（セッション）を壊さないための処理
            update_session_auth_hash(request, user)
            return redirect("families:family_settings")
    else:
        form = PasswordChangeForm(user=request.user)
        
    return render(request, "accounts/password_change.html", {"form": form})



@login_required
def user_profile_edit_view(request):
    # ログイン中のユーザー（＝自分）
    user = request.user
    
    if request.method == "POST":
        # POSTされた内容でフォームを作る（既存ユーザーを更新するため instance=user）
        form = UserProfileForm(request.POST, instance=user)
        
        # 入力チェック
        if form.is_valid():
            # DBに保存
            form.save()
            
            return redirect("families:family_settings")
        
        else:
            # GETのとき：すでに登録済みの値が入力欄に入った状態のフォームを作る
            form = UserProfileForm(instance=user)
        
        # ビューでuser = request.userとしており、このuserをテンプレで使いたいとき混乱しないようにuser_objという別名で渡している
        # テンプレでuserという名前がすでに別で使われている場合があり、この場合と混乱しないため   
        return render(request, "accounts/user_profile_edit.html", {"form": form, "user_obj":user})