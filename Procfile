web: gunicorn wsgi
beat: celery beat -A app -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
worker: celery worker -A app -l INFO
