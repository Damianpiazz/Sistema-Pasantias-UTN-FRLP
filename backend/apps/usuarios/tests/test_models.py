from apps.usuarios.models import User


def test_tiene_los_cinco_roles_del_documento():
    assert [rol.name for rol in User.Rol] == [
        "ADMIN_GENERAL",
        "EXTENSION",
        "SAE",
        "CONTABLE",
        "LEGAL",
    ]
