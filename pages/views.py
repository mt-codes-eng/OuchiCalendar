from django.shortcuts import render

def portfolio(request):
    return render(request, "pages/portfolio.html")
