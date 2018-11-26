from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from api import serializers
from app import models


class ArtistViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    authentication_classes = ()
    queryset = models.Artist.objects.all()
    serializer_class = serializers.ArtistSerializer
    lookup_field = "mbid"
