from nicegui import ui


def profile_header(title: str = "Profile", subtitle: str = None, icon: str = "person", authenticated: bool = True):
    """Reusable profile header component"""
    with ui.row().classes('items-center gap-3 mb-6 w-full'):
        # Icon
        ui.icon(icon, size='2.5rem').classes('text-primary')

        # Title and subtitle
        with ui.column().classes('gap-0'):
            ui.label(title).classes('text-3xl font-bold tracking-tight')
            if subtitle:
                ui.label(subtitle).classes('text-gray-500 text-sm')

        # Spacer and optional badge/status
        ui.space()

        # Status badge
        if authenticated:
            with ui.badge('✓ Online', color='positive').classes('text-sm'):
                pass
        else:
            with ui.badge('✗ Offline', color='negative').classes('text-sm'):
                pass
