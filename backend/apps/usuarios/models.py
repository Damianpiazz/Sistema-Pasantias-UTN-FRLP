from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuario nominal con el rol del area al que pertenece (RF01)."""

    class Rol(models.TextChoices):
        ADMIN_GENERAL = "ADMIN", "Administrador general"
        EXTENSION = "EXTENSION", "Extensión"
        SAE = "SAE", "SAE"
        CONTABLE = "CONTABLE", "Contable"
        LEGAL = "LEGAL", "Legal y Técnica"

    rol = models.CharField(max_length=20, choices=Rol.choices)
