from zoneinfo import ZoneInfo
from django.utils import timezone


class SystemTimezoneMiddleware:
    """Activate the hospital's saved timezone for each request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            from .models import SystemPreferences
            preferences = SystemPreferences.objects.filter(pk=1).first()
            zone_name = preferences.time_zone if preferences else 'Africa/Kampala'
            timezone.activate(ZoneInfo(zone_name))
        except Exception:
            timezone.activate(ZoneInfo('Africa/Kampala'))

        try:
            return self.get_response(request)
        finally:
            timezone.deactivate()
