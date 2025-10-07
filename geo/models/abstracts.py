from django.contrib.gis.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class GeoModel(models.Model):
    location = models.PointField(geography=True, blank=True, null=True)
    boundary = models.MultiPolygonField(geography=True, blank=True, null=True)

    class Meta:
        abstract = True


class PayloadModel(models.Model):
    raw_payload = models.JSONField(blank=True, null=True)
    meta = models.JSONField(blank=True, null=True)

    class Meta:
        abstract = True


class SourceTrackedModel(models.Model):
    source = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        abstract = True