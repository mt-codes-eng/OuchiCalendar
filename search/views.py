from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

@login_required
def search_view(request):
    """
    検索画面

    まずは検索画面を表示するだけ。
    このあと予定・記録の検索処理を追加していく。
    """

    context = {
        "today_str": timezone.localdate().strftime("%Y-%m-%d"),
    }

    return render(request, "search/search.html", context)