from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.utils import timezone
from .forms import SignUpForm, UserProfileForm
from families.models import Family
from invitations.models import Invitation
from color_assignments.models import FamilyColorAssignment

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
    """
    新規アカウント登録ビュー

    ・通常登録 → 新しいFamilyを作る
    ・招待URL経由 → 招待のFamilyに参加する
    ・招待トークンが無効なら 無効画面へ戻す
    ・登録時に選んだ個人カラーを FamilyColorAssignment に保存する
    """
    # ① 招待トークンを取得しておく
    # 例:/ouchi-calendar/signup/?invitation_token=abc123
    # GETで画面を開いたときは request.GET から
    # POSTでフォーム送信されたときは request.POST から取る
    if request.method == "POST":
        invitation_token = request.POST.get("invitation_token")
    else:
        invitation_token = request.GET.get("invitation_token")
    
    if request.method == "POST":
        # ② 送信されたデータ（記入済みの紙）でフォームを作る
        # 送信された文字データは request.POST、アップロードされた画像ファイルは request.FILES に入る
        # 画像アップロード対応のフォームでは、両方を渡す必要がある
        form = SignUpForm(request.POST, request.FILES)

        # ③ 入力チェック（メール形式、パスワード一致、強度など）
        if form.is_valid():
            # ④ 個人カラーを取り出す
            # SignUpForm の clean_color_code() で int に変換済み
            color_code = form.cleaned_data["color_code"]
            
            # ⑤ Userオブジェクトを作るけどまだDBには保存しない
            # 先に family をセットしたいので commit=False にする
            user = form.save(commit=False)
            
            # 招待オブジェクトを、あとで使えるように先に None で用意しておく
            invitation = None
            
            # ⑥ 招待URL経由かどうかで処理を分ける
            if invitation_token:
                try:
                    invitation = Invitation.objects.get(
                        invitation_token=invitation_token
                    )
                except Invitation.DoesNotExist:
                    invitation = None
                
                # 招待トークンが存在しない → 無効画面へ
                if not invitation:
                    return redirect("invitations:invalid")

                # すでに使用済み → 無効画面へ
                if invitation.status != Invitation.Status.UNUSED:
                    return redirect("invitations:invalid")

                # 期限切れ → status を EXPIRED にして無効画面へ
                if invitation.is_expired():
                    invitation.status = Invitation.Status.EXPIRED
                    invitation.save()
                    return redirect("invitations:invalid")
                
                # ここまで来たら有効な招待
                # 招待のfamilyに所属させる
                user.family = invitation.family
                
            else:
                # 通常登録（招待なし）
                # DBにFamilyレコードを1件作る
                # 家族名はあとで家族設定画面で入力する想定なので、まずは空文字で作成
                family = Family.objects.create(name="")
                # 紐づけ（さっき作ったfamilyを、Userのfamily欄に入れる）
                user.family = family
                
            try:
                with transaction.atomic():
                    # ⑦ Userを保存する
                    # SignUpForm は UserCreationForm を継承しているので、
                    # パスワードは平文ではなくハッシュ化されて安全に保存される
                    user.save()

                    # ⑧ 個人カラーを保存する
                    #
                    # update_or_create の意味：
                    # - すでにその user の色設定があれば更新
                    # - なければ新規作成
                    #
                    # signup直後は基本的に新規作成になるが、
                    # 今後の設計とも相性がよいのでこの形にしておく
                    FamilyColorAssignment.objects.update_or_create(
                        user=user, # user=user でその大人メンバーの色設定を探す。あれば更新。なければ新規作成
                        defaults={
                            "family": user.family,
                            "child": None,
                            "color_code": color_code,
                            "assign_type": FamilyColorAssignment.AssignType.USER,
                        }
                    )

            except IntegrityError:
                # ⑨ 家族内ですでに同じ色が使われているなど、
                # DBの一意制約に引っかかった場合
                #
                # このままだとユーザーには意味不明なエラーになるので、
                # フォームエラーとしてやさしく返す
                form.add_error(
                    "color_code",
                    "この色はすでに家族内で使われています。別の色を選択してください"
                )
                return render(
                    request,
                    "accounts/signup.html",
                    {
                        "form": form,
                        "invitation_token": invitation_token,
                    }
                )
            
            # ⑩ 有効な招待だった場合だけ使用済みにする
            if invitation_token and invitation:
                invitation.status = Invitation.Status.USED
                invitation.save()

            # ⑥ 自動ログイン。登録後、そのままログイン状態にする
            login(request, user)
            messages.success(request, "アカウント登録が完了しました")
            # ⑦ 遷移
            return redirect("families:family_settings")

    else:
        # GETのときは空のフォーム（空白の紙）を表示する
        # その型から作られた実物（インスタンス）。何も書かれていない入力用の紙を1枚用意した
        form = SignUpForm()
    
    context = {
        "form": form,
        "invitation_token": invitation_token,
    }

    # Python的に省略していない形はreturn render(request=request,template_name="accounts/signup.html",context={"form": form})
    # {"form": form}でその紙をHTMLに渡して、『accounts/signup.htmlに表示して』と頼んだ。テンプレート側で form を使えるように。辞書の意味：左 "form" → HTMLで使う名前、右 form → Pythonで作った申込書そのもの。
    return render(request, "accounts/signup.html", context)

    
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
    """
    自分のプロフィール編集ビュー

    この画面では、次の内容を変更できる
    - 名前
    - Email
    - 個人アイコン
    - 個人カラー

    個人カラーは User モデルではなく
    FamilyColorAssignment に保存する
    """
    # ログイン中のユーザー（＝自分）
    user = request.user
    
    if request.method == "POST":
        # プロフィール編集でも、画像ファイルが送られる可能性があるので
        # request.POST に加えて request.FILES も渡す
        # POSTされた内容でフォームを作る。instance=user を付けることで、新規作成ではなく「既存ユーザーの更新」になる
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        
        # 入力チェック
        if form.is_valid():
            # フォームで選んだ個人カラーを取り出す
            # clean_color_code() で int に変換済み
            color_code = form.cleaned_data["color_code"]

            try:
                # User の更新と、個人カラーの更新を
                # 「全部成功するか、全部やめるか」でまとめる
                with transaction.atomic():
                    # ① User本体を保存する
                    #    （名前、Email、画像 など）
                    form.save()

                    # ② 個人カラーを保存する
                    #
                    # update_or_create の意味：
                    # - すでにこの user の色設定があれば更新
                    # - まだなければ新規作成
                    #
                    # 既存ユーザーの中にはまだ色設定がない人もいるので、
                    # 「更新も新規作成もどちらも対応できる」この書き方が便利
                    FamilyColorAssignment.objects.update_or_create(
                        user=user,
                        defaults={
                            "family": user.family,
                            "child": None,  # 大人メンバーの個人カラーなので child は空
                            "color_code": color_code,
                            "assign_type": FamilyColorAssignment.AssignType.USER,
                        }
                    )

                # ここまで成功したら家族設定画面へ戻す
                return redirect("families:family_settings")

            except IntegrityError:
                # 同じ家族の中で、すでに別の人が使っている色を選んだ場合など
                # DBの一意制約エラーが起きることがある
                #
                # そのままエラー画面にせず、
                # 「個人カラー欄のエラー」として画面に戻す
                form.add_error(
                    "color_code",
                    "この色はすでに家族内で使われています。別の色を選択してください"
                )
        
    else:
        # GETのとき：登録済みの値が入力欄に入った状態のフォームを作る
        form = UserProfileForm(instance=user)
        
    # ビューでuser = request.userとしており、このuserをテンプレで使いたいとき混乱しないようにuser_objという別名で渡している
    # テンプレでuserという名前がすでに別で使われている場合があり、この場合と混乱しないため   
    return render(request, "accounts/user_profile_edit.html", {"form": form, "user_obj":user})