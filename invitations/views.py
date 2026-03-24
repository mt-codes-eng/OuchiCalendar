from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
import secrets

from .models import Invitation

@login_required
def invitation_create_view(request):
    """
    家族招待URLを発行して表示するビュー

    ・ログイン中ユーザーの家族に対する招待URLを作る
    ・すでに有効な未使用招待があればそれを再利用する
    ・なければ新しくトークンを発行する
    """

    # ----------------------------------------
    # ① ログイン中ユーザーの家族を取得
    # ----------------------------------------
    family = request.user.family

    # ----------------------------------------
    # ② 有効な未使用招待を探す
    # ----------------------------------------
    # 条件
    # ・同じ家族
    # ・未使用
    # ・期限がまだ切れていない
    invitation = Invitation.objects.filter(
        family=family,
        status=Invitation.Status.UNUSED,
        expires_at__gt=timezone.now(),
    ).order_by("-created_at").first()

    # ----------------------------------------
    # ③ なければ新しく招待を作る
    # ----------------------------------------
    if not invitation:
        # ランダムな安全なトークンを生成
        token = secrets.token_urlsafe(32)

        # 有効期限（72時間後）を作る
        expires_at = timezone.now() + timedelta(hours=72)

        # 招待レコードを作成
        invitation = Invitation.objects.create(
            family=family,
            invitation_token=token,
            expires_at=expires_at,
            status=Invitation.Status.UNUSED,
        )

    # ----------------------------------------
    # ④ 招待URLを作る
    # ----------------------------------------
    # URLのパス部分を作る
    invite_path = reverse(
        "invitations:accept",
        kwargs={"token": invitation.invitation_token},
    )

    # 絶対URLにする（http://localhost:8000/～）
    invite_url = request.build_absolute_uri(invite_path)

    # ----------------------------------------
    # ⑤ templateに渡す
    # ----------------------------------------
    context = {
        "invite_url": invite_url,
        "invitation": invitation,
    }

    return render(
        request,
        "invitations/invitation_create.html",
        context,
    )


def invitation_accept_view(request, token):
    """
    招待URLを受け取ったときのビュー
    
    ・URLに含まれる token から招待データを探す
    ・その招待が有効かどうか確認する
    ・有効なら新規アカウント登録画面へ案内する
    ・無効なら無効画面へ移動する
    """

    # ----------------------------------------
    # ① URLに入っている token に対応する招待データを取得する
    # ----------------------------------------
    # token が存在しない場合は 404ページ になる
    invitation = get_object_or_404(
        Invitation,
        invitation_token=token,
    )

    # ----------------------------------------
    # ② すでに使用済みなら無効画面へ
    # ----------------------------------------
    if invitation.status == Invitation.Status.USED:
        return redirect("invitations:invalid")

    # ----------------------------------------
    # ③ 期限切れかどうか確認する
    # ----------------------------------------
    # 期限切れなら status も EXPIRED に更新してから無効画面へ
    if invitation.is_expired(): # invitation.is_expired()はモデルに書いたメソッド
        invitation.status = Invitation.Status.EXPIRED
        invitation.save()
        return redirect("invitations:invalid")

    # ----------------------------------------
    # ④ まだログインしていない人は新規アカウント登録画面へ送る
    # ----------------------------------------
    # invitation_token をクエリパラメータで引き継ぐ
    # 例: /ouchi-calendar/signup/?invitation_token=abc123
    if not request.user.is_authenticated: # ログイン済みでないなら True,ログイン済みなら False
        signup_url = reverse("accounts:signup") # signup の URLを作る。/ouchi-calendar/signup/
        return redirect(f"{signup_url}?invitation_token={token}") # URLの後ろにクエリパラメータとして付ける。/ouchi-calendar/signup/?invitation_token=abc123xyz

    # ----------------------------------------
    # ⑤ すでにログイン済みの場合
    # ----------------------------------------
    # 今回の仕様では「URLをクリックした相手が新規登録する」流れが中心なので、
    # まずはログイン済みユーザーにも signup ではなく別画面に送るより、
    # シンプルに無効画面へ送る、または専用メッセージを出す方が安全
    #
    # 今回は簡単に invalid 画面へ送る
    return redirect("invitations:invalid")

def invitation_invalid_view(request):
    return HttpResponse("無効な招待URLです")
