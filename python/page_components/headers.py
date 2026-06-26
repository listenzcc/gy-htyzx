from datetime import datetime
from nicegui import ui


def reuseable_header(
        title: str = "Title",
        subtitle: str = None,
        icon: str = "person",
        badge_kwargs={'text': None, 'color': 'positive'}
):
    """
    Reusable header component

    ```layout
    [left] Title ----[space]---- colored badge [right]
    [left] subtitle -------------------------- [right]
    ```

    Args:
        title str: Title, default is "Title"
        subtitle str: Subtitle, default is None
        icon str: Icon name, default is persion
        badge_kwargs dict: Kwargs of badge, default is {'text': '--', 'color': 'positive'}
    """
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

        if badge_kwargs.get('text') is None:
            badge_kwargs['text'] = datetime.isoformat(datetime.now())

        with ui.badge(**badge_kwargs).classes('text-sm'):
            pass

        # Status badge
        # if authenticated:
        #     with ui.badge('✓ Online', color='positive').classes('text-sm'):
        #         pass
        # else:
        #     with ui.badge('✗ Offline', color='negative').classes('text-sm'):
        #         pass

        return
