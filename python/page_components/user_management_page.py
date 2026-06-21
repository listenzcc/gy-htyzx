from typing import List
from nicegui import ui
from datetime import datetime
from .inputs import date_input


def user_manager_header(title: str = "User Manager", icon: str = "person", n_users: int = 0):
    """Reusable user manager header component"""
    with ui.row().classes('items-center gap-3 mb-6 w-full'):
        # Icon
        ui.icon(icon, size='2.5rem').classes('text-primary')

        # Title and subtitle
        with ui.column().classes('gap-0'):
            ui.label(title).classes('text-3xl font-bold tracking-tight')

        # Spacer and optional badge/status
        ui.space()

        with ui.badge(f'Found {n_users} users', color='positive').classes('text-sm'):
            pass


def user_management_users_1(users: List[dict]):
    """
    Display users in a table.
    Clicking a row prints the corresponding user dict.
    """
    users = sorted(users, key=lambda e: e['id'])

    if not users:
        with ui.card().classes('w-full p-8 bg-gray-50'):
            ui.icon('people_outline', size='3rem').classes(
                'text-gray-400 mx-auto'
            )
            ui.label('No users found').classes(
                'text-gray-500 text-center text-lg'
            )
        return

    columns = [
        {
            'name': 'id',
            'label': 'ID',
            'field': 'id',
            'sortable': True,
            'align': 'left',
        },
        {
            'name': 'username',
            'label': 'Username',
            'field': 'username',
            'sortable': True,
            'align': 'left',
        },
        {
            'name': 'role',
            'label': 'Role',
            'field': 'role',
            'sortable': True,
            'align': 'left',
        },
        {
            'name': 'is_active',
            'label': 'Status',
            'field': 'is_active',
            'sortable': True,
            'align': 'left',
        },
        {
            'name': 'created_at',
            'label': 'Created',
            'field': 'created_at',
            'sortable': True,
            'align': 'left',
        },
    ]

    rows = []
    user_map = {}

    for user in users:
        user_id = user.get('id')
        user_map[user_id] = user

        status = (
            '<span class="text-green-600">🟢 Active</span>'
            if user.get('is_active')
            else '<span class="text-red-600">🔴 Inactive</span>'
        )

        created = user.get('created_at')

        if isinstance(created, datetime):
            created = created.strftime('%Y-%m-%d %H:%M')

        elif isinstance(created, str):
            try:
                dt = datetime.fromisoformat(
                    created.replace('Z', '+00:00')
                )
                created = dt.strftime('%Y-%m-%d %H:%M')
            except Exception:
                pass

        role_colors = {
            'ADMIN': 'bg-red-100 text-red-800',
            'USER': 'bg-blue-100 text-blue-800',
            'GUEST': 'bg-gray-100 text-gray-800',
        }

        role_class = role_colors.get(
            user.get('role'),
            'bg-gray-100 text-gray-800'
        )

        role_html = (
            f'<span class="px-2 py-1 rounded {role_class}">'
            f'{user.get("role", "—")}'
            f'</span>'
        )

        rows.append({
            'id': user_id,
            'username': user.get('username', '—'),
            'role': role_html,
            'is_active': status,
            'created_at': created or '—',
        })

    with ui.card().classes('w-full shadow-lg border'):

        with ui.row().classes(
            'w-full justify-between items-center p-4 bg-gray-50 rounded-t border-b'
        ):
            ui.label('User List').classes(
                'text-xl font-semibold'
            )

        with ui.table(
            rows=rows,
            columns=columns,
            row_key='id',
            pagination={'rowsPerPage': 10},
        ).classes('w-full').props(
            'dense bordered flat'
        ) as table:

            def on_row_click(e):
                row = e.args[1]
                user = user_map.get(row['id'])

                if user:
                    print(user)
                else:
                    print(f'Invalid user')

            table.on('row-click', on_row_click)
            table.add_slot(
                'body-cell-role',
                r'''
                <q-td :props="props">
                    <span v-html="props.value"></span>
                </q-td>
                '''
            )
            table.add_slot(
                'body-cell-is_active',
                r'''
                <q-td :props="props">
                    <span v-html="props.value"></span>
                </q-td>
                '''
            )

        with ui.row().classes(
            'w-full justify-between items-center p-2 bg-gray-50 rounded-b border-t'
        ):
            ui.label(
                f'Total: {len(users)} users'
            ).classes(
                'text-sm text-gray-500'
            )

            ui.button(
                'Export CSV',
                icon='download'
            ).props(
                'outline'
            ).on_click(
                lambda: ui.notify(
                    f'Exporting {len(users)} users...'
                )
            )


def user_management_users(users: List[dict], id: int, user_service, on_edit_apply=None):
    users = sorted(users, key=lambda e: e['id'])

    if not users:
        with ui.card().classes('w-full p-8 bg-gray-50'):
            ui.icon('people_outline', size='3rem').classes(
                'text-gray-400 mx-auto')
            ui.label('No users found').classes(
                'text-gray-500 text-center text-lg')
        return

    selected = {'user': None}

    columns = [
        {'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
        {'name': 'username', 'label': 'Username',
            'field': 'username', 'sortable': True},
        {'name': 'role', 'label': 'Role', 'field': 'role', 'sortable': True},
        {'name': 'is_active', 'label': 'Status',
            'field': 'is_active', 'sortable': True},
        {'name': 'created_at', 'label': 'Created',
            'field': 'created_at', 'sortable': True},
    ]

    rows = []
    user_map = {}

    for user in users:
        user_map[user['id']] = user

        status = (
            '<span class="text-green-600">🟢 Active</span>'
            if user.get('is_active')
            else '<span class="text-red-600">🔴 Inactive</span>'
        )

        created = user.get('created_at')
        if isinstance(created, datetime):
            created = created.strftime('%Y-%m-%d %H:%M')
        elif isinstance(created, str):
            try:
                created = datetime.fromisoformat(created.replace(
                    'Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            except Exception:
                pass

        role_colors = {
            'ADMIN': 'bg-red-100 text-red-800',
            'USER': 'bg-blue-100 text-blue-800',
            'GUEST': 'bg-gray-100 text-gray-800',
        }

        role_class = role_colors.get(
            user.get('role'),
            'bg-gray-100 text-gray-800'
        )

        role_html = (
            f'<span class="px-2 py-1 rounded {role_class}">'
            f'{user.get("role", "—")}'
            f'</span>'
        )

        rows.append({
            'id': user['id'],
            'username': user.get('username', '—'),
            'role': role_html,
            'is_active': status,
            'created_at': created or '—',
        })

    # --- UI layout: table + detail panel ---

    # List users table
    with ui.card().classes('w-full shadow-lg border'):
        ui.label('User List').classes('text-lg font-semibold')
        with ui.table(
            rows=rows,
            columns=columns,
            row_key='id',
            pagination={'rowsPerPage': 10},
        ).classes('w-full').props('dense bordered flat') as table:

            def select_row(e):
                row = e.args[1]
                selected['user'] = user_map.get(row['id'])
                render_detail()

            table.on('row-click', select_row)

            table.add_slot('body-cell-role', r'''
                <q-td :props="props"><span v-html="props.value"></span></q-td>
            ''')
            table.add_slot('body-cell-is_active', r'''
                <q-td :props="props"><span v-html="props.value"></span></q-td>
            ''')

    # detail edit table
    with ui.card().classes('w-full shadow-lg border') as detail_card:
        ui.label('Selected User').classes('text-lg font-semibold')

        inputs = {}

        def render_detail():
            if not user_service.get_user_by_id(id).has_permission('edit_users'):
                return

            detail_card.clear()

            with detail_card:
                ui.label('User Detail').classes('text-lg font-semibold')

                u = selected['user']
                if not u:
                    ui.label('Select a user').classes('text-gray-500')
                    return

                # immutable fields (grey / disabled)
                ui.input('ID', value=u.get('id')).props(
                    'disable').classes('bg-gray-100')
                ui.input('UUID', value=u.get('uuid')).props(
                    'disable').classes('bg-gray-100')
                ui.input('Username', value=u.get('username')).props(
                    'disable').classes('bg-gray-100')

                # editable fields
                inputs['role'] = ui.select(
                    options=['ADMIN', 'USER', 'GUEST'],
                    label='Role',
                    value=u.get('role')
                )
                inputs['is_active'] = ui.switch(
                    'Active', value=u.get('is_active'))

                # date handling
                # Birth
                birth = u.get('birth_date')
                inputs['birth_date'] = date_input('Birth Date', birth)

                # Training
                training = u.get('training_date')
                inputs['training_date'] = date_input('Training Date', training)

                # Apply
                def apply():
                    updated = dict(u)

                    updated['role'] = inputs['role'].value
                    updated['is_active'] = inputs['is_active'].value
                    updated['birth_date'] = inputs['birth_date'].value or None
                    updated['training_date'] = inputs['training_date'].value or None

                    if on_edit_apply:
                        on_edit_apply(updated)
                    else:
                        print('APPLY:', updated)

                    ui.notify('Changes prepared')

                ui.button('Apply', on_click=apply).props('color=primary')
    return
