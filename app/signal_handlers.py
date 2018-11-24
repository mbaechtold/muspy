from django.db.models.signals import post_save
from django.dispatch import receiver

from app import models
from app import tasks


@receiver(post_save, sender=models.ReleaseGroup)
def notify_user(sender, instance, created, **kwargs):
    """
    Notify the users about new releases.
    """
    if created:
        if not instance.is_deleted and instance.date and instance.type:
            user_artists = models.UserArtist.objects.filter(artist=instance.artist)
            for user_artist in user_artists:
                profile = user_artist.user.profile
                if profile.notify and profile.email_activated:
                    types = profile.get_types()
                    if instance.type in types:
                        tasks.notify_user.delay(
                            user_pk=user_artist.user.pk, release_group_pk=instance.pk
                        )
