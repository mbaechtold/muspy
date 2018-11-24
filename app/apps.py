from django.apps import AppConfig


class MuspyApp(AppConfig):
    name = "app"

    def ready(self):
        import app.signal_handlers  # noqa
