def role_context(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'current_role': getattr(request.user, 'role', 'patient'),
        'current_role_label': request.user.get_role_display() if hasattr(request.user, 'get_role_display') else 'Patient',
        'user_initials': request.user.initials() if hasattr(request.user, 'initials') else 'U',
    }


def system_preferences_context(request):
    """Expose the saved regional display formats to every rendered page."""
    from .models import SystemPreferences

    try:
        preferences, _ = SystemPreferences.objects.get_or_create(pk=1)
        return {
            'system_currency': preferences.currency,
            'system_date_format': preferences.date_format,
            'system_time_format': 'H:i' if preferences.time_format == '24' else 'h:i A',
            'system_time_zone': preferences.time_zone,
        }
    except Exception:
        # Keep the application usable if preferences are temporarily unavailable.
        return {
            'system_currency': 'UGX',
            'system_date_format': 'd/m/Y',
            'system_time_format': 'H:i',
            'system_time_zone': 'Africa/Kampala',
        }
