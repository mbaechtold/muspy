from django.contrib import admin
from app import models


class ReleaseGroupAdminInline(admin.TabularInline):
    model = models.ReleaseGroup
    extra = 1


@admin.register(models.Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "mbid"]
    list_display_links = ["name"]
    inlines = [ReleaseGroupAdminInline]


@admin.register(models.Job)
class JobAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ReleaseGroup)
class ReleaseGroupAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "mbid", "artist"]
    list_display_links = ["name"]


@admin.register(models.Star)
class StarAdmin(admin.ModelAdmin):
    pass


@admin.register(models.UserArtist)
class UserArtistAdmin(admin.ModelAdmin):
    pass


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(models.UserSearch)
class UserSearchAdmin(admin.ModelAdmin):
    pass
