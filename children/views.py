# children/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Child
from .forms import ChildForm
from django.db import transaction, IntegrityError
from color_assignments.models import FamilyColorAssignment

@login_required
def child_create_view(request):
    if request.method == "POST":
        # 送信されたデータ（記入済みの紙）でフォームを作る
        form = ChildForm(request.POST, request.FILES)
        
        if form.is_valid():
            # フォームで選んだ個人カラーを取り出す
            color_code = form.cleaned_data["color_code"]
            # フォームに入っているデータを使って、Childオブジェクトを作る
            # Child(name="たろう", image_url="aaa")というようなChild型のオブジェクトをPythonの中で作る。
            child = form.save(commit=False)
            # 作ったChildオブジェクトに family を後から代入している
            # ログイン中のユーザーが所属している家族をchildren_childテーブルのfamily欄に入れる
            child.family = request.user.family
            
            try:
                # 子ども保存と色保存を、全部成功するか全部やめるかでまとめる
                with transaction.atomic():
                    # ① 子ども本体を保存
                    child.save()

                    # ② 子どもの個人カラーを保存
                    FamilyColorAssignment.objects.update_or_create(
                        child=child,
                        defaults={
                            "family": child.family,
                            "user": None,  # 子どもカラーなので user は空
                            "color_code": color_code,
                            "assign_type": FamilyColorAssignment.AssignType.CHILD,
                        }
                    )

                return redirect("families:family_settings")

            except IntegrityError:
                # すでに家族内で使われている色を選んだ場合など
                form.add_error(
                    "color_code",
                    "この色はすでに家族内で使われています。別の色を選択してください"
                )

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
            # フォームで選んだ個人カラーを取り出す
            color_code = form.cleaned_data["color_code"]
            # 今回新しく画像が選ばれたか確認
            new_image = form.cleaned_data.get("image")

            try:
                # 子ども更新と色更新を、全部成功するか全部やめるかでまとめる
                with transaction.atomic():
                    # ① 子ども本体を保存
                    form.save()

                    # ② 子どもの個人カラーを保存
                    FamilyColorAssignment.objects.update_or_create(
                        child=child,
                        defaults={
                            "family": child.family,
                            "user": None,  # 子どもカラーなので user は空
                            "color_code": color_code,
                            "assign_type": FamilyColorAssignment.AssignType.CHILD,
                        }
                    )

                # 新しい画像が送られていて、画像が差し替わったときだけ古い画像を削除
                if new_image and old_image and old_image != child.image:
                    old_image.delete(save=False)

                return redirect("families:family_settings")

            except IntegrityError:
                form.add_error(
                    "color_code",
                    "この色はすでに家族内で使われています。別の色を選択してください"
                )

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
    
    # GETで直接このURLに来た場合は、削除確認画面を出さず編集画面へ戻す
    return redirect("children:child_edit", pk=child.pk)