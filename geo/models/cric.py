from django.contrib.gis.db import models
from django.utils import timezone

from geo.models.abstracts import GeoModel, TimeStampedModel, PayloadModel, SourceTrackedModel

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

SENSOR_TYPE_CHOICES = [
    ("soil_moisture", "Soil Moisture"),
    ("temperature", "Temperature"),
    ("humidity", "Humidity"),
    ("ndvi", "NDVI"),
    ("hardness", "Hardness"),
]


class Stadium(GeoModel, TimeStampedModel):
    """Represents a cricket stadium and its spatial location."""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    country = models.CharField(max_length=80, blank=True, null=True)
    capacity = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def __str__(self):
        return self.name


class StadiumFeature(models.Model):
    """Static stadium features like soil type, drainage, or altitude."""
    stadium = models.ForeignKey(Stadium, on_delete=models.CASCADE, related_name="features")
    key = models.CharField(max_length=80)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ("stadium", "key")

    def __str__(self):
        return f"{self.stadium.name} - {self.key}"


class Pitch(TimeStampedModel):
    """Represents a specific cricket pitch within a stadium."""
    stadium = models.ForeignKey(Stadium, on_delete=models.CASCADE, related_name="pitches")
    name = models.CharField(max_length=120, default="Main")
    area = models.PolygonField(geography=True, blank=True, null=True)
    centroid = models.PointField(geography=True, blank=True, null=True)
    length_m = models.FloatField(blank=True, null=True)
    width_m = models.FloatField(blank=True, null=True)
    surface_type = models.CharField(max_length=32, choices=SURFACE_CHOICES, default="grass")
    preferred_usage = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["stadium", "name"])]

    def __str__(self):
        return f"{self.stadium.name} — {self.name}"


class PitchSnapshot(TimeStampedModel, PayloadModel, SourceTrackedModel):
    """Time-series data snapshot representing pitch conditions at a given time."""
    pitch = models.ForeignKey(Pitch, on_delete=models.CASCADE, related_name="snapshots")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    soil_moisture = models.FloatField(blank=True, null=True)
    humidity = models.FloatField(blank=True, null=True)
    temperature_c = models.FloatField(blank=True, null=True)
    grass_cover_pct = models.FloatField(blank=True, null=True)
    ndvi = models.FloatField(blank=True, null=True)
    hardness = models.FloatField(blank=True, null=True)
    predicted_condition = models.CharField(max_length=32, choices=PITCH_CONDITION_CHOICES, blank=True, null=True)
    predicted_confidence = models.FloatField(blank=True, null=True)
    measure_point = models.PointField(geography=True, blank=True, null=True)

    class Meta:
        ordering = ["-timestamp"]
        get_latest_by = "timestamp"
        indexes = [models.Index(fields=["pitch", "timestamp"])]

    def __str__(self):
        return f"{self.pitch} @ {self.timestamp:%Y-%m-%d %H:%M}"


class SoilSample(PayloadModel):
    """Represents a soil sample taken at a specific pitch location."""
    pitch = models.ForeignKey(Pitch, on_delete=models.CASCADE, related_name="soil_samples")
    taken_at = models.DateTimeField()
    sample_point = models.PointField(geography=True)
    ph = models.FloatField(blank=True, null=True)
    organic_matter_pct = models.FloatField(blank=True, null=True)
    nitrogen_mgkg = models.FloatField(blank=True, null=True)
    phosphorus_mgkg = models.FloatField(blank=True, null=True)
    potassium_mgkg = models.FloatField(blank=True, null=True)
    lab_report = models.FileField(upload_to="soil_reports/", blank=True, null=True)

    def __str__(self):
        return f"SoilSample {self.pitch} at {self.taken_at.date()}"


class SensorDevice(PayloadModel):
    """Represents an IoT or virtual device installed on a pitch."""
    uid = models.CharField(max_length=120, unique=True)
    label = models.CharField(max_length=120, blank=True, null=True)
    device_type = models.CharField(max_length=80, choices=SENSOR_TYPE_CHOICES)
    installed_at = models.DateTimeField(blank=True, null=True)
    last_heartbeat = models.DateTimeField(blank=True, null=True)
    pitch = models.ForeignKey(Pitch, on_delete=models.SET_NULL, null=True, blank=True, related_name="devices")

    def __str__(self):
        return f"{self.uid} ({self.device_type})"


class SensorReading(PayloadModel):
    """Represents a single sensor reading from a device."""
    device = models.ForeignKey(SensorDevice, on_delete=models.CASCADE, related_name="readings")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    value = models.FloatField()
    unit = models.CharField(max_length=32, blank=True, null=True)
    location = models.PointField(geography=True, blank=True, null=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["device", "timestamp"])]

    def __str__(self):
        return f"{self.device.uid} @ {self.timestamp:%Y-%m-%d %H:%M} = {self.value}"


class BaseImage(PayloadModel, TimeStampedModel):
    """Base abstract image model shared between satellite and drone images."""
    pitch = models.ForeignKey(Pitch, on_delete=models.CASCADE, related_name="%(class)ss", null=True, blank=True)
    acquired_at = models.DateTimeField(db_index=True)
    footprint = models.PolygonField(geography=True)
    provider = models.CharField(max_length=80)
    file_url = models.CharField(max_length=1024, blank=True, null=True)

    class Meta:
        abstract = True


class SatelliteImage(BaseImage):
    """Satellite-derived image for NDVI or soil moisture."""
    product_id = models.CharField(max_length=200, blank=True, null=True)
    derived_indices = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.provider} {self.acquired_at.date()}"


class CameraImage(BaseImage):
    """Drone or camera-captured image for detailed pitch view."""
    image_file = models.FileField(upload_to="camera_images/")
    view_point = models.PointField(geography=True, blank=True, null=True)


class Team(models.Model):
    """Represents a cricket team."""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=80, blank=True, null=True)

    def __str__(self):
        return self.name


class Player(PayloadModel):
    """Represents an individual player."""
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="players")
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80, blank=True, null=True)
    jersey_no = models.PositiveIntegerField(blank=True, null=True)
    role = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name or ''}".strip()


class Match(TimeStampedModel, PayloadModel):
    """Represents a match and its metadata."""
    pitch = models.ForeignKey(Pitch, on_delete=models.SET_NULL, null=True, blank=True, related_name="matches")
    stadium = models.ForeignKey(Stadium, on_delete=models.SET_NULL, null=True, blank=True, related_name="matches")
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    teams = models.ManyToManyField(Team, related_name="matches")

    def __str__(self):
        return f"{self.name} ({self.start_date.date()})"


class Inning(models.Model):
    """Represents an inning in a match."""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="innings")
    number = models.PositiveSmallIntegerField()
    batting_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, related_name="batting_innings")
    bowling_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, related_name="bowling_innings")
    overs = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = [["match", "number"]]


class Over(models.Model):
    """Represents a single over within an inning."""
    inning = models.ForeignKey(Inning, on_delete=models.CASCADE, related_name="over_set")
    number = models.PositiveSmallIntegerField()
    bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = [["inning", "number"]]


class Delivery(PayloadModel):
    """Represents an individual ball delivery event."""
    over = models.ForeignKey(Over, on_delete=models.CASCADE, related_name="deliveries")
    ball_in_over = models.PositiveSmallIntegerField()
    batsman = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="batting_deliveries")
    bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="bowling_deliveries")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    pitch_point = models.PointField(geography=True, blank=True, null=True)
    impact_point = models.PointField(geography=True, blank=True, null=True)
    landing_distance = models.FloatField(blank=True, null=True)
    speed_kmph = models.FloatField(blank=True, null=True)
    spin_rpm = models.FloatField(blank=True, null=True)
    outcome = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["timestamp"])]


class PlayerTrackPoint(PayloadModel):
    """Stores timestamped player positions for motion tracking."""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="track_points")
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="track_points")
    timestamp = models.DateTimeField(db_index=True)
    location = models.PointField(geography=True)
    speed = models.FloatField(blank=True, null=True)
    heading = models.FloatField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["match", "player", "timestamp"])]


class PitchMetric(TimeStampedModel):
    """Aggregated computed pitch metrics for daily or seasonal summaries."""
    pitch = models.ForeignKey(Pitch, on_delete=models.CASCADE, related_name="metrics")
    date = models.DateField(db_index=True)
    avg_soil_moisture = models.FloatField(blank=True, null=True)
    avg_ndvi = models.FloatField(blank=True, null=True)
    avg_grass_cover = models.FloatField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = [["pitch", "date"]]


class PitchAnalysis(TimeStampedModel):
    """Stores machine learning outputs like predictions or classifications."""
    snapshot = models.ForeignKey(PitchSnapshot, on_delete=models.CASCADE, related_name="analyses")
    model_name = models.CharField(max_length=120)
    model_version = models.CharField(max_length=50, blank=True, null=True)
    prediction = models.CharField(max_length=120)
    confidence = models.FloatField(blank=True, null=True)
    details = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["model_name", "created_at"])]


class IngestionEvent(TimeStampedModel, PayloadModel):
    """Tracks external data ingestions for debugging and traceability."""
    source = models.CharField(max_length=120)
    finished_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=32, default="pending")
    items_processed = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.source} @ {self.created_at:%Y-%m-%d %H:%M}"
