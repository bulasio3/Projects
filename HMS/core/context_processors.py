def role_context(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'current_role': getattr(request.user, 'role', 'patient'),
        'current_role_label': request.user.get_role_display() if hasattr(request.user, 'get_role_display') else 'Patient',
        'user_initials': request.user.initials() if hasattr(request.user, 'initials') else 'U',
    }