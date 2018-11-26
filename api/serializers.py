from django.contrib.auth.models import User
from rest_framework import serializers

from app import models


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Artist
        fields = ("mbid", "name", "disambiguation", "sort_name")
        lookup_field = "mbid"
        extra_kwargs = {"url": {"lookup_field": "mbid"}}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email", "groups")
