from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Schedule

@login_required
def month_view(request):
    context = {}
    return render(request, "schedule/month.html", context)


@login_required
def day_view(request, date):
    schedules =Schedule.objects.filter(
        family = request.user.family
    )
    
    context = {
        "date": date,
        "schedules": schedules,
    }

    return render(request, "schedule/day.html", context)


@login_required
def create_choice_view(request, date):
    context = {
        "date": date,
    }
    
    return render(request, "schedule/create_choice.html", context)


@login_required
def schedule_create_view(request):
    context = {
        "mode": "create",
    }
    return render(request, "schedule/schedule_form.html", context)
    
    
@login_required
def schedule_detail_view(request, pk):
    schedule = get_object_or_404(
        Schedule,
        pk=pk,
        family=request.user.family
    )
    
    context = {
        "schedule": schedule,
    }
    
    return render(request, "schedule/schedule_detail.html", context)
    
    
@login_required
def schedule_edit_view(request, pk):
    schedule = get_object_or_404(
        Schedule,
        pk=pk,
        family = request.user.family
    )
    
    context = {
        "mode": "edit",
        "schedule": schedule,
    }
    
    return render(request, "schedule/schedule_form.html", context)
    
    
@login_required
def schedule_delete_view(request, pk):
    schedule = get_object_or_404(
        Schedule,
        pk=pk,
        family = request.user.family
    )
    
    context = {
        "schedule": schedule,
    }
    
    return render(request, "schedule/schedule_confirm_delete.html", context)