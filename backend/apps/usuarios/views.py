from django.contrib.auth.views import LoginView, LogoutView


class IniciarSesion(LoginView):
    template_name = "registration/login.html"


class CerrarSesion(LogoutView):
    pass
