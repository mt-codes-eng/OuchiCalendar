from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("accounts:login")
    
    return redirect("schedule:month")

@login_required
def howto_view(request):
    next_url = request.GET.get("next")
    
    context = {
        "next_url": next_url,        
    }
    
    return render(request, "core/howto.html", context,)

    

