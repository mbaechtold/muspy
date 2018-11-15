web: gunicorn wsgi
beat: celery beat --app=app worker --loglevel=INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
worker: celery worker --app=app worker --loglevel=INFO
