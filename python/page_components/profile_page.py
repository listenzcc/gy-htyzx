from nicegui import ui
from datetime import datetime


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


def profile_content_readonly(user: dict):
    # Create a nicely styled table
    with ui.card().classes('w-full mx-auto p-6'):
        ui.label('User Information').classes('text-xl font-semibold mb-4')

        # Define field labels and formatting
        fields = [
            ('Name', 'name'),
            ('User ID', 'id'),
            ('UUID', 'uuid'),
            ('Role', 'role'),
            ('Status', 'is_active'),
            ('Email', 'email'),  # If exists
            ('Gender', 'gender'),
            ('Birth Date', 'birth_date'),
            ('Education', 'education'),
            ('Training Date', 'training_date'),
            ('Created At', 'created_at'),
            ('Last Login', 'last_login'),
            ('Session ID', 'session_id'),
        ]

        # Create table
        with ui.table(rows=[], columns=[
            {'name': 'field', 'label': 'Field', 'field': 'field', 'sortable': True},
            {'name': 'value', 'label': 'Value', 'field': 'value', 'sortable': True},
        ]).classes('w-full').props('dense bordered flat') as table:

            # Build rows
            rows = []
            for label, key in fields:
                value = user.get(key)

                # Format datetime objects
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, bool):
                    value = '✓ Active' if value else '✗ Inactive'
                elif value == '':
                    value = 'Not provided'

                rows.append({'field': label, 'value': value})

            # Add authenticated status
            rows.append({
                'field': 'Authenticated',
                'value': '✓ Yes' if user.get('authenticated', False) else '✗ No'
            })

            # Add login time
            login_time = user.get('logInTime')
            if login_time:
                if isinstance(login_time, datetime):
                    login_time = login_time.strftime('%Y-%m-%d %H:%M:%S')
                rows.append({'field': 'Login Time', 'value': login_time})

            table.rows = rows
