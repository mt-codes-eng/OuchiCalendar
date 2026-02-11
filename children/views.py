# children/views.py
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Child

@login_required
def child_list_view(request):
    # クエリ（DB検索）を実行
    # Child → children_childテーブルを操作するためのモデル。Djangoのモデルクラスは「DBとつながった特別なクラス」
    # objects → DB検索・DB操作をするための道具箱（窓口）
    # Child.objects → テーブルを操作するための担当者。テーブル操作係
    # .filter(...) → 条件をつけて絞り込み
    # .order_by("id") → 並び順を指定
    # family が request.user.family の子どもだけに絞る = ログイン中のユーザーの家族に属する子どもだけを取得する
    children = Child.objects.filter(family=request.user.family).order_by("id")
    return render(request, "children/child_list.html", {"children": children})

@login_required
def child_create_view(request):
    return HttpResponse("child_create")

@login_required
def child_edit_view(request, pk):
    return HttpResponse(f"child_edit {pk}")

@login_required
def child_delete_view(request, pk):
    return HttpResponse(f"child_delete {pk}")