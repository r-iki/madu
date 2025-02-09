web: gunicorn core.wsgi --chdir src --bind 0.0.0.0:$PORT
web: uvicorn core.asgi:application --chdir src --host=0.0.0.0 --port=${PORT:-8000}

