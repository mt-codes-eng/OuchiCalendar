from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import ScheduleComment

@login_required
def comment_recent_view(request):
    """
    コメント新着画面
    """

    comments = (
        ScheduleComment.objects
        .select_related("schedule", "from_user", "to_user", "schedule__user")
        .filter(
            # Q(...) | Q(...) | Q(...)：または条件
            Q(from_user=request.user) | # 自分が投稿したコメント
            Q(to_user=request.user) | # 自分宛てのコメント
            Q(schedule__user=request.user) # 自分が担当者の予定についたコメント
        )
        .order_by("-created_at")
        .distinct()[:20] # 最初は20件表示とする
    )

    context = {
        "comments": comments,
    }

    return render(request, "comments/comment_recent.html", context)