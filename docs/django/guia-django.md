# Django — fundamentos operativos

Referencia técnica para trabajar en el SGPC. Cubre el ciclo de vida de una request, el ORM,
las migraciones, la autenticación y el tooling del repo.

Stack del proyecto: Python 3.14 · Django 6.1 · Django REST Framework · PostgreSQL 17 · pytest.

---

## 1. Ciclo de vida de una request

Django sigue el patrón MTV (Model–Template–View), equivalente al MVC con otros nombres:
el *model* accede a los datos, el *view* orquesta la lógica de la request, el *template*
produce la salida HTML.

```
cliente → gunicorn (o runserver)
        → middleware[]            security, whitenoise, sessions, csrf, auth, messages
        → URLconf (config.urls)   resuelve la URL → vista + parámetros
        → vista                    consulta modelos, arma contexto, renderiza
        → respuesta inversa por middleware[]
        → cliente
```

- Cada middleware es una capa que puede mutar `request`/`response` o cortar el ciclo
  (p. ej. CSRF rechaza con 403 antes de que la vista se ejecute).
- Si ninguna ruta matchea, el router lanza `Resolver404`.
- El servidor es síncrono (WSGI). No hay código async en el proyecto y no hace falta.

## 2. Estructura del repo

| Ruta | Rol |
|---|---|
| `backend/manage.py` | CLI de Django; define `DJANGO_SETTINGS_MODULE=config.settings` |
| `backend/config/settings.py` | configuración única (django-environ, apps, DB, static) |
| `backend/config/urls.py` | URLconf raíz: monta `core`, `cuentas/`, `admin/` |
| `backend/apps/<app>/` | una app por módulo de la EDT (ver §10) |
| `backend/requirements.txt` | dependencias (pip freeze) |
| `pyproject.toml` | config de ruff y pytest (corre desde la raíz) |
| `compose.yml` | servicios `db` (Postgres 17) y `app` (build desde `./backend`) |

Las apps se registran en `INSTALLED_APPS`. Sin registrarse, Django no descubre sus modelos,
ni sus templates (`APP_DIRS`), ni sus migraciones, ni su admin.

## 3. URLconf y vistas

```python
# backend/config/urls.py
urlpatterns = [
    path("", include("apps.core.urls")),
    path("cuentas/", include("apps.usuarios.urls")),
    path("admin/", admin.site.urls),
]
```

- `path(ruta, vista, name="...")`: `name` es la referencia estable — en templates se usa
  `{% url 'home' %}` y en código `reverse("home")`. Renombrar una ruta no rompe nada si
  el `name` se mantiene.
- `include()` delega en el `urls.py` de cada app; el prefijo se define en la raíz.
- Vistas: function-based views en este proyecto. Firma tipo:

```python
def home(request: HttpRequest) -> HttpResponse:
    return render(request, "core/home.html")
```

- La vista valida la request, llama a `services` y devuelve la respuesta. No contiene
  reglas de negocio (ver §10).
- Excepciones útiles: `Http404` → 404, `PermissionDenied` → 403.
- El frontend JSON se sirve desde `apps/<app>/api/` con DRF (serializers + ViewSets).

## 4. Motor de templates

- Búsqueda: primero `TEMPLATES.DIRS` (vacío en este proyecto), después
  `apps/<app>/templates/` en orden de `INSTALLED_APPS`. Por eso `base.html` vive en
  `apps/core/templates/base.html` y es accesible desde cualquier app.
- Herencia: `{% extends "base.html" %}` + bloques `{% block content %}`.
- `{{ variable }}` escapa HTML por defecto (anti-XSS); `|safe` solo ante contenido
  que ya sabés que es confiable.
- En formularios: `{% csrf_token %}` es obligatorio (si no, el middleware CSRF rechaza 403).
- Estáticos: `{% static 'ruta' %}`; en prod los sirve whitenoise desde `STATIC_ROOT`
  (collectstatic los copia ahí; gunicorn no sirve estáticos por sí mismo).
- Context processors agregan variables a todos los templates (`request`, `user`, `messages`).

## 5. ORM

El ORM mapea clases a tablas y atributos a columnas. Cada campo es un descriptor: valida,
serializa y traduce a SQL. El SQL se genera por consulta — no hay capa de acceso manual.

### 5.1 Modelos y campos

```python
class User(AbstractUser):
    class Rol(models.TextChoices):
        ADMIN_GENERAL = "ADMIN", "Administrador general"
        SAE = "SAE", "SAE"

    rol = models.CharField(max_length=20, choices=Rol.choices)
```

Campos en uso frecuente:

| Campo | Uso |
|---|---|
| `CharField(max_length)` | strings cortos; `choices` para enumeraciones cerradas |
| `TextField` | texto largo (objetos de convenio, observaciones) |
| `DecimalField(max_digits, decimal_digits)` | montos — nunca `FloatField` para dinero |
| `DateField` / `DateTimeField` | fechas; `auto_now_add`/`auto_now` para timestamps |
| `BooleanField` | flags (p. ej. baja lógica) |
| `FileField(upload_to=)` | documentos PDF/imagen (RF05/15/21) |
| `ForeignKey(to, on_delete)` | relación N:1 (ver §5.3) |

Convenciones:

- `null` es para la columna SQL; `blank` para el formulario. En strings conviene
  `blank=True` + `""` (no `null=True`).
- `__str__` obligatorio: es lo que muestra el admin y los logs.
- `default` evita columnas vacías en escrituras nuevas; no reescribe filas existentes.
- Modelos abstractos (`class Meta: abstract = True`) no generan tabla: es el mecanismo
  de los mixins compartidos (`TimeStampedModel`, `SoftDeleteModel`) en `core`.

### 5.2 Managers y QuerySets

Un `QuerySet` es **lazy**: no ejecuta SQL hasta ser evaluado (iterar, `list()`, `len()`,
`bool()`). Las cadenas de métodos devuelven un QuerySet nuevo, así que se pueden componer.

```python
convenios = Convenio.objects.filter(estado="FINALIZADO", vencimiento__lt=hoy)  # sin SQL aún
total = convenios.count()                                                      # SELECT COUNT(...)
```

Operaciones de escritura:

- `obj.save()` actualiza la fila completa (objeto ya persistido).
- `QuerySet.update(**kw)` actualiza por lote sin instanciar objetos; no dispara `save()`.
- `Model.objects.create(**kw)` = instanciar + `save()` en una llamada.
- `get()` lanza `DoesNotExist` o `MultipleObjectsReturned` — para listados usar `filter()`.

Filtros combinados: `filter(cond_a).filter(cond_b)` es AND; `filter(Q(a) | Q(b))` es OR;
excluir con `exclude()`. Campos con `__`: `vencimiento__lt`, `empresa__cuit__startswith`.

**Caché del QuerySet:** una vez evaluado, cachea su resultado. Reutilizarlo no repite la
consulta; agregarle un filtro posterior crea uno nuevo y vuelve a consultar.

**Agregaciones:** `aggregate(total=Sum("monto"))`, `values("empresa").annotate(n=Count("id"))`.

### 5.3 Relaciones

| Tipo | Traducción | Ejemplo del dominio |
|---|---|---|
| `ForeignKey` | columna con FK, many-to-one | `Convenio.empresa` |
| `OneToOneField` | FK + `unique` | extensión de un modelo base |
| `ManyToManyField` | tabla intermedia | `Convenio.especialidades` |
| `related_name` | alias del acceso inverso | `empresa.convenios.all()` |

`on_delete` define qué pasa con el hijo cuando muere el padre:

- `CASCADE` — borra en cascada (usar solo donde la dependencia es total; recordar RN17:
  en este sistema casi nada se borra, priman bajas lógicas).
- `PROTECT` — impide el borrado si tiene hijos (típico para datos con facturas/enlaces).
- `SET_NULL` — deja la referencia en `NULL` (requiere `null=True`).

#### N+1

```python
# Mal: 1 consulta de convenios + 1 por cada convenio para traer la empresa
for c in Convenio.objects.all():
    print(c.empresa.razon_social)

# Bien: JOIN en una sola consulta
for c in Convenio.objects.select_related("empresa").all():
    print(c.empresa.razon_social)
```

Regla: `select_related("campo")` para `ForeignKey`/`OneToOne` (hace JOIN);
`prefetch_related("campo")` para `ManyToMany` y relaciones inversas (trae en un lote
adicional). Ante cualquier listado que toca relaciones, revisar con `django.test.utils`
o el debug toolbar si hay un `+1`.

### 5.4 Validación y transacciones

- `Model.save()` **no** ejecuta validaciones de negocio. `full_clean()` valida pero tampoco
  corre solo. En este repo la validación de reglas (RN01–RN19) vive en `services.py` y se
  invoca explícitamente antes de persistir.
- Restricciones a nivel DB (únicas, FKs) son la última línea: `unique=True` sobre CUIT
  garantiza la regla aunque dos requests lleguen a la vez.
- `transaction.atomic()` agrupa escrituras múltiples en una sola unidad: o se aplican
  todas o ninguna (p. ej. crear factura + sus líneas).

```python
with transaction.atomic():
    factura = Factura.objects.create(...)
    FacturaPasante.objects.create(factura=factura, ...)
```

- Señales (`post_save`, etc.): útiles para ganchos transversales como la auditoría (RF03).
  La lógica de negocio no va en señales — es invisible desde la vista y difícil de testear.

### 5.5 ContentType — relaciones polimórficas

Para la app `seguimiento`, una `Nota` (RF26) debe apuntar a empresa, convenio, pasantía
o factura sin heredar de una clase común. Django resuelve esto con el framework
`contenttypes`:

```python
content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
object_id = models.PositiveIntegerField()
objeto = GenericForeignKey("content_type", "object_id")  # no es un campo de DB
```

`Nota.objects.filter(content_type=ct, object_id=empresa.pk)` devuelve las notas de esa
empresa. Es el patrón estándar para notas, auditoría y cualquier "adjunto a lo que sea".

## 6. Migraciones

Una migración es un archivo `.py` declarativo que representa un cambio en el esquema.
Las migraciones son código: se versionan, se commitean y viajan con su modelo.

### 6.1 Flujo

```
modelos (código)  --makemigrations-->  archivo 000N_*.py  --migrate-->  schema en la DB
```

- `makemigrations` **solo escribe el archivo**; no toca la base.
- `migrate` aplica los archivos pendientes a la DB conectada (cada entorno tiene su
  propio estado: sqlite local, Postgres de docker, la DB de test).

### 6.2 Comandos

| Comando | Qué hace |
|---|---|
| `manage.py makemigrations <app>` | genera la migración de los modelos cambiados |
| `manage.py migrate` | aplica las pendientes |
| `manage.py migrate <app> 0002` | retrocede hasta una versión (si es reversible) |
| `manage.py showmigrations` | estado por app: `[ ]` pendiente, `[X]` aplicada |
| `manage.py sqlmigrate <app> 000N` | imprime el SQL sin ejecutarlo |
| `manage.py makemigrations --check --dry-run` | falla si hay modelos sin migrar (CI) |

### 6.3 Reglas del equipo

1. La migración se commitea **junto con el modelo**, en el mismo PR. Nunca un modelo
   mergeado sin su migración.
2. No editar una migración ya commiteada: los compañeros que la aplicaron quedan con
   un checksum distinto y la historia diverge. Se genera una nueva migración que
   corrige.
3. Las migraciones aplicadas se limpian con un entorno nuevo, no a mano.
4. `AUTH_USER_MODEL` (`usuarios.User`) se define **antes** de la primera migración y no
   se cambia después: todo `ForeignKey` al user depende de él (`swappable_dependency`).
5. Una app recién creada necesita su `0001_initial`. El repo ya pasó por esto: sin ella,
   `runserver` falla con `Dependency on app with no migrations: usuarios` porque
   `admin/0001` depende del modelo de usuario.

### 6.4 Migraciones y tests

pytest-django crea la DB de test corriendo `migrate` con los archivos existentes. Por eso:

- un modelo sin migración rompe cualquier test que use la base (pese a que `check` pase);
- tests marcados sin `django_db` no tocan la base y no la necesitan;
- `pytest --reuse-db` reutiliza la DB de test entre corridas (acelera el ciclo local);
  con cambios de esquema, `--create-db` la reconstruye.

## 7. Admin y autenticación

- `django.contrib.admin` en `admin/` descubre los `ModelAdmin` registrados con
  `@admin.register(Model)`. Es el ABM de respaldo mientras no exista la pantalla propia.
- `AUTH_USER_MODEL = "usuarios.User"`: un único modelo de usuario para auth y dominio,
  con `rol` (`User.Rol`) y datos de la persona. Nunca importar
  `django.contrib.auth.models.User` directo — usar `get_user_model()`.
- Contraseñas: Django guarda solo el hash (PBKDF2 por defecto); `set_password()` /
  `check_password()`.
- Sesiones: tabla `django_session` con cookie firmada. `LoginView` la crea al autenticar
  (`/cuentas/login/`), `LogoutView` la destruye.
- Autorización: `is_staff`/`is_superuser` para el admin; `Permission` y `Group` son el
  mecanismo nativo para la matriz de roles (RF02, RN18). El rol por área (`User.rol`)
  es el criterio del dominio; la denegación por rol se implementará con decoradores o
  mixins sobre ese campo.
- Toda vista que requiere login: `@login_required` (o `LoginRequiredMixin`); la redirección
  usa `LOGIN_URL = "login"`.

## 8. Configuración

- `settings.py` único, con `django-environ`. Variables en `.env` en la raíz del repo
  (la lee tanto `compose` como Django). Nunca commitear `.env`.
- `DATABASE_URL` no definida → SQLite (`backend/db.sqlite3`). Definida → Postgres
  (servicio `db` de compose). El mismo código corre en ambos.
- `DEBUG=True` solo en desarrollo: en prod desactiva archivos estáticos servidos por
  Django y muestra rutas internas en los errores. `ALLOWED_HOSTS` debe listar los
  dominios reales.
- Email: en Django 6.1 el bloque correcto es `MAILERS` (`EMAIL_BACKEND` está deprecado).
  En desarrollo, backend consola — los mails se imprimen en la terminal.
- Comandos de settings en runtime:

```python
from django.conf import settings
from django.contrib.auth import get_user_model

settings.DEBUG          # cualquier setting
User = get_user_model() # modelo de usuario correcto (nunca el import directo)
```

## 9. Tests

- Corredor: pytest + pytest-django. Settings y paths en `pyproject.toml`
  (`DJANGO_SETTINGS_MODULE`, `pythonpath = ["backend"]`, markers).
- Dos markers: `unit` (lógica de `services` y modelos, sin HTTP) e `integration`
  (endpoints vía el fixture `client`).

```python
import pytest

pytestmark = pytest.mark.integration

def test_home_renderiza(client):
    assert client.get("/").status_code == 200
```

- Tests que crean o leen datos llevan `@pytest.mark.django_db`. La base de test se
  crea y migra automáticamente y se trunca entre tests.
- Datos de prueba: `factory_boy` (`tests/factories.py` por app). No fabricar datos con
  fixtures gigantes cuando una factory alcanza.
- Ejecución: `pytest`, `pytest -m unit`, `pytest -m integration`,
  `pytest backend/apps/usuarios` (un path puntual).
- Lint: `ruff check .` antes de commitear.

## 10. Capas del proyecto

Estructura repetida en cada app:

```
backend/apps/<app>/
├── models.py      # schema y comportamiento de persistencia
├── services.py    # reglas de negocio (RN01–RN19); el lugar de la lógica
├── views.py       # vistas template: HTTP in, HttpResponse out
├── urls.py        # rutas de la app
├── admin.py       # registro en admin
├── api/           # DRF: serializers.py, views.py, urls.py
├── templates/<app>/
└── tests/{factories.py, unit/, integration/}
```

Flujo de una llamada:

```
request → views.py → services.py → models/QuerySets → services → views → response
```

Reglas de la casa:

- `views.py` no contiene reglas de negocio: valida la request, delega en `services`,
  elige template o serializa.
- `models.py` no conoce HTTP. Reglas que cruzan modelos (duración de pasantía, tope de
  18 meses, vigencia de convenio) van en `services.py`.
- `services.py` es testeable sin HTTP — de ahí salen los tests `unit`.
- La API (`api/`) es una fachada sobre los mismos services; no duplica lógica.

## 11. Comandos de uso diario

```powershell
# local
venv\Scripts\python.exe backend\manage.py runserver
venv\Scripts\python.exe backend\manage.py makemigrations
venv\Scripts\python.exe backend\manage.py migrate
venv\Scripts\python.exe backend\manage.py shell       # consola ORM
venv\Scripts\python.exe -m pytest
venv\Scripts\python.exe -m ruff check .

# docker
docker compose up -d --build
docker compose exec app python manage.py migrate      # cwd dentro de la imagen es /app
docker compose logs -f app
docker compose down
```

## 12. Errores habituales

| Síntoma | Causa | Solución |
|---|---|---|
| `Dependency on app with no migrations: X` | app con modelos sin `0001_initial` | `makemigrations <app>` |
| `You have unapplied migrations` | modelos cambiados sin migrar | `makemigrations` + `migrate` |
| `no such table` en tests | el modelo no tiene migración en el repo | commitear la migración |
| `CSRF verification failed` (403) | falta `{% csrf_token %}` en el form | agregarlo |
| `NOT NULL constraint failed` | `null=False` y el campo llega vacío | default o `blank=True` según corresponda |
| `column does not exist` | migración no aplicada en esa base | `migrate` en esa base |
| `debug toolbar` muestra queries repetidas | N+1 | `select_related` / `prefetch_related` |
| `TemplateDoesNotExist` | template fuera de `templates/` o mal referenciado | revisar ruta y `INSTALLED_APPS` |
| `STATIC` 404 en gunicorn/docker | no se corrió `collectstatic` | correrlo (el entrypoint ya lo hace) |
