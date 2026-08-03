"""Template context for the "Remember Dashboard" (view mode) feature."""

from .decorators import VIEW_MODE_MESSAGE


def view_mode(request):
    """Expose view-mode state to every template.

    ``display_user``  - whose data is on screen (the logged-in user normally, the
                        remembered user in view mode).
    ``is_view_mode``  - True only for a remembered browser with no live session.
    """
    is_view_mode = getattr(request, 'is_view_mode', False)

    return {
        'is_view_mode': is_view_mode,
        'remembered_user': getattr(request, 'remembered_user', None),
        'display_user': getattr(request, 'display_user', None) or getattr(request, 'user', None),
        'view_mode_message': VIEW_MODE_MESSAGE,
    }
