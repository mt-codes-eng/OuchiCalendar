from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

@login_required
def settings_view(request):
    family = request.user.family
    
    # どこから来たか取得
    next_url = request.GET.get("next")
    
    context = {
        "family": family,
        "next_url": next_url,
    }

    return render(request, "core/settings.html", context,)

@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("accounts:login")
    return render(request, "core/logout_confirm.html")

@login_required
def howto_view(request):
    return render(request, "core/howto.html")

    

