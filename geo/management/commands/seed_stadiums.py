from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point, Polygon
from geo.models import Stadium, Pitch

class Command(BaseCommand):
    help = "Seed 10 famous international cricket stadiums (excluding India) with sample pitches"

    def handle(self, *args, **options):
        stadiums_data = [
            {"name": "Lord's Cricket Ground", "country": "England", "coords": (51.5281, -0.1720)},
            {"name": "Melbourne Cricket Ground", "country": "Australia", "coords": (-37.8199, 144.9834)},
            {"name": "Eden Park", "country": "New Zealand", "coords": (-36.8485, 174.7670)},
            {"name": "The Oval", "country": "England", "coords": (51.4826, -0.1122)},
            {"name": "SCG - Sydney Cricket Ground", "country": "Australia", "coords": (-33.8912, 151.2241)},
            {"name": "Wellington Regional Stadium", "country": "New Zealand", "coords": (-41.3048, 174.7815)},
            {"name": "Old Trafford Cricket Ground", "country": "England", "coords": (53.4560, -2.2910)},
            {"name": "Kensington Oval", "country": "Barbados", "coords": (13.0936, -59.6100)},
            {"name": "Queen's Park Oval", "country": "Trinidad & Tobago", "coords": (10.6541, -61.5168)},
            {"name": "Newlands", "country": "South Africa", "coords": (-33.9460, 18.4647)},
        ]

        for data in stadiums_data:
            stadium, created = Stadium.objects.get_or_create(
                name=data["name"],
                defaults={
                    "country": data["country"],
                    "location": Point(data["coords"][1], data["coords"][0])  # lon, lat
                }
            )

            if created:
                # Create a sample pitch polygon around the stadium centroid
                lat, lon = data["coords"]
                delta = 0.0003  # small area around the centroid
                polygon = Polygon((
                    (lon - delta, lat - delta),
                    (lon - delta, lat + delta),
                    (lon + delta, lat + delta),
                    (lon + delta, lat - delta),
                    (lon - delta, lat - delta),
                ))

                Pitch.objects.create(
                    stadium=stadium,
                    name="Main Pitch",
                    area=polygon,
                    centroid=stadium.location,
                    surface_type="grass",
                    current_condition="balanced"
                )

                self.stdout.write(self.style.SUCCESS(f"Created stadium and pitch: {stadium.name}"))
            else:
                self.stdout.write(f"Stadium already exists: {stadium.name}")
