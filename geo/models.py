from django.contrib.gis.db import models

SURFACE_CHOICES = [
    ("grass", "Grass"),
    ("dry", "Dry"),
    ("dusty", "Dusty"),
    ("green", "Green Top"),
    ("artificial", "Artificial"),
]

PITCH_CONDITION_CHOICES = [
    ("batting_friendly", "Batting friendly"),
    ("bowling_friendly", "Bowling friendly"),
    ("balanced", "Balanced"),
]


class Stadium(models.Model):
    """Cricket stadium with location info."""
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=120, blank=True, null=True)
    country = models.CharField(max_length=80, blank=True, null=True)
    location = models.PointField(geography=True, blank=True, null=True)  # stadium centroid

    def __str__(self):
        return self.name


class Pitch(models.Model):
    """Specific pitch within a stadium for visualization."""
    stadium = models.ForeignKey(Stadium, on_delete=models.CASCADE, related_name="pitches")
    name = models.CharField(max_length=120, default="Main")
    area = models.PolygonField(geography=True, blank=True, null=True)
    centroid = models.PointField(geography=True, blank=True, null=True)
    surface_type = models.CharField(max_length=32, choices=SURFACE_CHOICES, default="grass")
    current_condition = models.CharField(max_length=32, choices=PITCH_CONDITION_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.stadium.name} — {self.name}"
