from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "core/home.html")


def health(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok", content_type="text/plain")
