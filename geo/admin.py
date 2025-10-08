# geo/admin.py
from django.contrib import admin
from .models import Stadium, Pitch


@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "country")
    search_fields = ("name", "city", "country")


@admin.register(Pitch)
class PitchAdmin(admin.ModelAdmin):
    list_display = ("name", "stadium", "surface_type", "current_condition")
    list_filter = ("surface_type", "current_condition", "stadium")
    search_fields = ("name", "stadium__name")
