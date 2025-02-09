from django.contrib import admin

# Register your models here.
from .models import SpectralReading
class SpectralReadingAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'name',)
    list_filter = ('name',)
admin.site.register(SpectralReading, SpectralReadingAdmin)