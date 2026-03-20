# children/views.py
from django.shortcuts import render, redirect, get_object_or_404
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
        form = ChildForm(request.POST, request.FILES)
        
        if form.is_valid():
            # フォームに入っているデータを使って、Childオブジェクトを作る
            # Child(name="たろう", image_url="aaa")というようなChild型のオブジェクトをPythonの中で作る。
            child = form.save(commit=False)
            # 作ったChildオブジェクトに family を後から代入している
            # ログイン中のユーザーが所属している家族をchildren_childテーブルのfamily欄に入れる
            child.family = request.user.family
            child.save()
            return redirect("families:family_settings")
        
    else:
        form = ChildForm()
        
    return render(request, "children/child_form.html", {"form": form})

@login_required
def child_edit_view(request, pk):
    # pk=pk：URLの <int:pk> で渡された数字IDの子どものデータを探す
    # family=request.user.family：ログイン中の家族の子どもだけに限定する（権限漏れ防止）
    # ① 編集対象の子どもを取得（他家族のデータは取れないようにする。「他人の子どもをURL直打ちで編集」が防ぐ）
    child = get_object_or_404(Child, pk=pk, family=request.user.family)
    
    if request.method == "POST":
        old_image = child.image
        
        # ② POST：送信された内容で「既存childを更新するフォーム」を作る
        form = ChildForm(request.POST, request.FILES, instance=child)
        
        if form.is_valid():
            new_image = form.cleaned_data.get("image")
            form.save()
            if new_image and old_image and old_image != child.image:
                old_image.delete(save=False)
            return redirect("families:family_settings")
        
    else:
        # ③ GET：最初に画面を開いたとき、既存データ入りのフォームを作る
        form = ChildForm(instance=child)
    
    return render(request, "children/child_form.html", {"form":form, "child":child})

@login_required
def child_delete_view(request, pk):
    # ① 削除対象の子どもを取得（他家族のデータは取れないようにする。「他人の子どもをURL直打ちで編集」が防ぐ）
    child = get_object_or_404(Child, pk=pk, family=request.user.family)
    
    if request.method == "POST":
        if child.image:
            child.image.delete(save=False)
            
        # ② POST：DBから削除する
        child.delete()
        return redirect("families:family_settings")
    
    return render(request, "children/child_confirm_delete.html", {"child":child})