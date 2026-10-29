#!/bin/sh
set -e

# Con argumentos se ejecuta el comando pedido (p. ej. python manage.py migrate).
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

python manage.py collectstatic --noinput
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2
