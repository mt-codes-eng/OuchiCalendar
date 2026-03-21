from django.shortcuts import render
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
    return HttpResponse(f"招待受け取り: {token}")

def invitation_invalid_view(request):
    return HttpResponse("無効な招待URLです")
