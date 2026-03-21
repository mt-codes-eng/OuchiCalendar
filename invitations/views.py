from django.shortcuts import render
from django.http import HttpResponse

def invitation_create_view(request):
    return HttpResponse("招待作成画面")

def invitation_accept_view(request, token):
    return HttpResponse(f"招待受け取り: {token}")

def invitation_invalid_view(request):
    return HttpResponse("無効な招待URLです")
