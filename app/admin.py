from django.contrib import admin

from app import models


class ReleaseGroupAdminInline(admin.TabularInline):
    model = models.ReleaseGroup
    extra = 1


@admin.register(models.Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "mbid", "last_check_for_releases"]
    list_display_links = ["name"]
    search_fields = ["name"]
    inlines = [ReleaseGroupAdminInline]


@admin.register(models.Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "type"]


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "release_group"]


@admin.register(models.ReleaseGroup)
class ReleaseGroupAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "name",
        "mbid",
        "date",
        "artist",
        "cover_art_url",
        "last_check_for_cover_art",
    ]
    list_display_links = ["name"]
    list_filter = ["is_deleted", "type"]
    search_fields = ["name"]


@admin.register(models.Star)
class StarAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "release_group"]


@admin.register(models.UserArtist)
class UserArtistAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "artist", "date"]


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "email_activated"]


@admin.register(models.UserSearch)
class UserSearchAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "search"]
