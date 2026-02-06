from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def family_settings_view(request):
    # ログインしているユーザー(request.user)の家族を取り出してfamily という変数に入れる
    family = request.user.family
    return render(request, "families/family_settings.html", {"family": family})
