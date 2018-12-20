from django.contrib import admin

from django_safari_notifications import models


admin.site.register(models.Domain)

admin.site.register(models.DomainNames)

admin.site.register(models.Token)
