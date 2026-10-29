from django.urls import path

from apps.usuarios import views

urlpatterns = [
    path("login/", views.IniciarSesion.as_view(), name="login"),
    path("logout/", views.CerrarSesion.as_view(), name="logout"),
]
