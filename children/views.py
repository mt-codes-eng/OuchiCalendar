from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def child_list_view(request):
    return HttpResponse("child_list")

@login_required
def child_create_view(request):
    return HttpResponse("child_create")

@login_required
def child_edit_view(request, pk):
    return HttpResponse(f"child_edit {pk}")

@login_required
def child_delete_view(request, pk):
    return HttpResponse(f"child_delete {pk}")