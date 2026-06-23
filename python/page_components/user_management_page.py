import sys
from typing import List
from nicegui import ui
from datetime import datetime
from .inputs import date_input

sys.path.append('..')  # noqa
from auth.user_service import UserService

ROLE_COLORS = {
    'ADMIN': 'bg-red-100 text-red-800',
    'USER': 'bg-blue-100 text-blue-800',
    'GUEST': 'bg-gray-100 text-gray-800',
}

GENDER_COLORS = {
    'male': 'text-blue-800',
    'female': 'text-red-800'
}

EDUCATIONS = [
    'middle school',      # 初中
    'high school',        # 高中
    'associate degree',   # 大专
    'bachelor',           # 本科
    'master',             # 硕士
    'doctorate'           # 博士
]


def user_manager_header(title: str = "User Manager", icon: str = "person"):
    """Reusable user manager header component"""
    with ui.row().classes('items-center gap-3 mb-6 w-full'):
        # Icon
        ui.icon(icon, size='2.5rem').classes('text-primary')

        # Title and subtitle
        with ui.column().classes('gap-0'):
            ui.label(title).classes('text-3xl font-bold tracking-tight')

        # Spacer and optional badge/status
        ui.space()

        with ui.badge('List Users', color='positive').classes('text-sm'):
            pass


def user_management_users(id: int, user_service: UserService, on_edit_apply=None):
    users = sorted([e.to_dict()
                   for e in user_service.list_users()], key=lambda e: e['id'])

    if not users:
        with ui.card().classes('w-full p-8 bg-gray-50'):
            ui.icon('people_outline', size='3rem').classes(
                'text-gray-400 mx-auto')
            ui.label('No users found').classes(
                'text-gray-500 text-center text-lg')
        return

    selected = {'user': None}

    columns = [
        dict(name='id', label='ID'),
        dict(name='username', label='Username'),
        dict(name='role', label='Role'),
        dict(name='gender', label='Gender'),
        dict(name='birth_date', label='BirthDate'),
        dict(name='training_date', label='TrainingDate'),
        dict(name='education', label='Education'),
        dict(name='is_active', label='IsActive'),
        dict(name='created_at', label='CreatedAt'),
    ]

    [e.update({'field': e['name'], 'sortable': True}) for e in columns]

    rows = []
    user_map = {}

    # user is dict
    for user in users:
        user_map[user['id']] = user

        is_active = (
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

        role_class = ROLE_COLORS.get(
            user.get('role'),
            'bg-gray-100 text-gray-800'
        )

        role = (
            f'<span class="px-2 py-1 rounded {role_class}">'
            f'{user.get("role", "—")}'
            f'</span>'
        )

        gender_class = GENDER_COLORS.get(
            user.get('gender'),
            'text-gray-800'
        )

        gender = (
            f'<span class="px-2 py-1 rounded {gender_class}">'
            f'{user.get("gender", "—")}'
            f'</span>'
        )

        rows.append({
            'id': user['id'],
            'username': user['username'],
            'role': role,
            'is_active': is_active,
            'created_at': created or '—',
            'training_date': user['training_date'],
            'birth_date': user['birth_date'],
            'education': user['education'],
            'gender': gender
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

            for cell in ['role', 'is_active', 'gender']:
                table.add_slot(f'body-cell-{cell}', r'''
                    <q-td :props="props"><span v-html="props.value"></span></q-td>
                ''')

    # detail edit table
    with ui.card().classes('w-1/3 shadow-lg border') as detail_card:
        ui.label('Select a user').classes('text-lg font-semibold')

        inputs = {}

        def render_detail():

            detail_card.clear()

            with detail_card:
                if not user_service.get_user_by_id(id).has_permission('edit_users'):
                    ui.label('Permission Deny').classes('text-red-800')
                    return

                ui.label('User Detail').classes('text-lg font-semibold')

                u = selected['user']
                if not u:
                    ui.label('Select a user').classes('text-gray-500')
                    return

                # immutable fields (grey / disabled)
                with ui.row():
                    ui.input('ID', value=u.get('id')).props(
                        'disable').classes('bg-gray-100')
                    inputs['is_active'] = ui.switch(
                        'Active', value=u.get('is_active'))
                ui.input('Username', value=u.get('username')).props(
                    'disable').classes('bg-gray-100')
                ui.input('UUID', value=u.get('uuid')).props(
                    'disable').classes('w-full bg-gray-100')

                # Role & gender
                with ui.row().classes('w-full'):
                    inputs['role'] = ui.select(
                        options=['ADMIN', 'USER', 'GUEST'],
                        label='Role',
                        value=u.get('role')
                    ).classes('w-1/3')
                    inputs['gender'] = ui.select(
                        options=['male', 'female'],
                        label='Gender',
                        value=u.get('gender')
                    ).classes('w-1/3')

                # With date handling
                # Birth
                birth = u.get('birth_date')
                inputs['birth_date'] = date_input(
                    'Birth Date', birth.strftime('%Y-%m-%d'))

                # Training
                training = u.get('training_date')
                inputs['training_date'] = date_input(
                    'Training Date', training.strftime('%Y-%m-%d'))

                # Education
                education = u.get('education')
                options = [e for e in EDUCATIONS]
                if not education in options:
                    options.append(education)
                inputs['education'] = ui.select(
                    options=options,
                    value=education,
                    label='Education',
                    new_value_mode='add'
                )

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
                        print(f'APPLY, {updated=}')

                    ui.notify('Changes prepared')

                ui.button('Apply', on_click=apply).props('color=primary')
    return
