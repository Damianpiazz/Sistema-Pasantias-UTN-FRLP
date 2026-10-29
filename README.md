# Sistema de Gestión de Pasantías y Convenios (SGPC)

Aplicación web para la gestión de empresas, convenios y pasantías de la Universidad
Tecnológica Nacional, Facultad Regional La Plata.

Stack: Python 3.14 · Django 6.1 · Django REST Framework · PostgreSQL 17.

## Requisitos

- Python 3.14
- Git
- Docker Desktop (solo para el flujo con PostgreSQL)

## Instalación

Clonar el repositorio y crear el entorno virtual:

```bash
git clone <url-del-repositorio>
cd Sistema-Pasantias-UTN-FRLP
python -m venv venv
```

Activar el entorno virtual:

```powershell
# Windows PowerShell
venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source venv/bin/activate
```

Instalar las dependencias:

```bash
python -m pip install -r backend/requirements.txt
```

## Variables de entorno

El archivo `.env.example` en la raíz es la plantilla. Crear el `.env` local:

```bash
cp .env.example .env
```

| Variable | Default | Descripción |
|---|---|---|
| `SECRET_KEY` | valor de desarrollo | clave de firmado de sesiones y tokens. Reemplazar fuera de desarrollo. |
| `DEBUG` | `True` | `False` en producción. Con `True` Django sirve estáticos y muestra trazas de errores. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | dominios aceptados, separados por coma. |
| `DATABASE_URL` | sin definir → SQLite | `postgres://usuario:clave@host:5432/base`. Comentar para usar SQLite. |

`.env` está en `.gitignore`: no se commitea. El mismo archivo lo lee `compose.yml` para
interpolar las variables del servicio `app`.

## Levantar el backend

### Opción A: Docker (aplicación + PostgreSQL)

```powershell
docker compose up -d --build
```

Queda en http://localhost:8000. Los servicios `app` y `db` arrancan con healthcheck;
`app` espera a que `db` esté `healthy`.

### Opción B: entorno virtual local (SQLite por defecto)

```powershell
python backend/manage.py migrate
python backend/manage.py runserver
```

Queda en http://127.0.0.1:8000.

### Opción C: entorno virtual local con PostgreSQL

```powershell
docker compose up -d db                    # solo la base
# descomentar DATABASE_URL en .env (apunta a localhost:5432)
python backend/manage.py migrate
python backend/manage.py runserver
```

### Primer arranque

`migrate` crea el esquema en la base conectada. Para acceder al admin (`/admin/`):

```powershell
python backend/manage.py createsuperuser
```

En Docker el prefijo de manage.py cambia porque el working directory del contenedor es `/app`:

```powershell
docker compose exec app python manage.py migrate
docker compose exec app python manage.py createsuperuser
```

Cuando cambien modelos, generar la migración y commitearla junto con el modelo:

```powershell
python backend/manage.py makemigrations
python backend/manage.py migrate
```

## Tests y lint

```powershell
python -m pytest                 # todos
python -m pytest -m unit         # unitarios
python -m pytest -m integration   # contra endpoints
python -m ruff check .           # lint
```

## Estructura

```
backend/            aplicación Django: manage.py, config/, apps/, Dockerfile, requirements.txt
docs/               ADRs, TDDs y guías (docs/django/)
compose.yml         servicios db (PostgreSQL) y app
.env.example        plantilla de variables de entorno
pyproject.toml      configuración de ruff y pytest
conftest.py         fixtures compartidas de pytest
```

## Documentación

- `docs/django/guia-django.md` — fundamentos de Django, ORM y migraciones
- `docs/ADRs/` — decisiones de arquitectura
- `docs/TDDs/` — documentos de diseño técnico
