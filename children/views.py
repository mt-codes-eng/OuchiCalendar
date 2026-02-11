# children/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Child
from .forms import ChildForm

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
    if request.method == "POST":
        # 送信されたデータ（記入済みの紙）でフォームを作る
        form = ChildForm(request.POST)
        
        if form.is_valid():
            # フォームに入っているデータを使って、Childオブジェクトを作る
            # Child(name="たろう", image_url="aaa")というようなChild型のオブジェクトをPythonの中で作る。
            child = form.save(commit=False)
            # 作ったChildオブジェクトに family を後から代入している
            # ログイン中のユーザーが所属している家族をchildren_childテーブルのfamily欄に入れる
            child.family = request.user.family
            child.save()
            return redirect("children:child_list")
        
    else:
        form = ChildForm()
        
    return render(request, "children/child_form.html", {"form": form})

@login_required
def child_edit_view(request, pk):
    return HttpResponse(f"child_edit {pk}")

@login_required
def child_delete_view(request, pk):
    return HttpResponse(f"child_delete {pk}")