import sys
import pandas as pd

from nicegui import ui
from pathlib import Path
from datetime import datetime

from .inputs import date_input

sys.path.append('..')  # noqa
from constants import *
from auth.user_service import UserService

password_validation = {
    '密码过短': lambda value: len(value) > 5,
    '密码包含不支持的字符': lambda value: all([e in ALLOWED_PASSWORD for e in value])
}


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

    # Filter state
    filters = {
        'username': '',
        'role': None,
        'gender': None,
        'education': None,
        'is_active': None,
        'birth_date_from': None,
        'birth_date_to': None,
        'training_date_from': None,
        'training_date_to': None,
    }

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

        role_class = ROLES.get(
            user.get('role'),
            STYLES.plainText
        )

        role = (
            f'<span class="px-2 py-1 rounded {role_class}">'
            f'{user.get("role", "—")}'
            f'</span>'
        )

        gender_class = GENDERS.get(
            user.get('gender'),
            STYLES.plainText
        )

        gender = (
            f'<span class="px-2 py-1 rounded {gender_class}">'
            f'{user.get("gender", "—")}'
            f'</span>'
        )

        education_class = EDUCATIONS.get(
            user.get('education'),
            STYLES.plainText
        )

        education = (
            f'<span class="px-2 py-1 rounded {education_class}">'
            f'{user.get("education", "—")}'
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
            'education': education,
            'gender': gender
        })

    # --- UI layout: table + detail panel ---

    # Filter section
    # .classes('w-full mb-4 p-4 bg-gray-50'):
    # with ui.card().classes(STYLES.fullCard):
    with ui.expansion('Click to Toggle Filter', icon='menu').classes('w-full'):
        # .classes('text-lg font-bold mb-2')
        ui.label('Filters').classes(STYLES.cardTitleLabel)

        row_styles = 'w-full gap-4 justify-center items-center'

        with ui.row().classes(row_styles):
            # Role filter
            filters['role_input'] = ui.select(
                options=['All'] + list(ROLES),
                label='Role',
                value='All'
            ).classes('w-1/5')

            # Gender filter
            filters['gender_input'] = ui.select(
                options=['All'] + list(GENDERS),
                label='Gender',
                value='All'
            ).classes('w-1/5')

            # Education filter
            filters['education_input'] = ui.select(
                options=['All'] + list(EDUCATIONS),
                label='Education',
                value='All'
            ).classes('w-1/5')

            # Status filter
            filters['status_input'] = ui.select(
                options=['All', 'Active', 'Inactive'],
                label='Status',
                value='All'
            ).classes('w-1/5')

        with ui.row().classes(row_styles):
            # with ui.column().classes('gap-2'):
            filters['birth_date_from'] = date_input(
                'Birth date from', None).classes('w-1/5')
            filters['birth_date_to'] = date_input(
                'Birth date to', None).classes('w-1/5')

            # with ui.column().classes('gap-2'):
            filters['training_date_from'] = date_input(
                'Training date from', None).classes('w-1/5')
            filters['training_date_to'] = date_input(
                'Training date to', None).classes('w-1/5')

        # Action buttons
        with ui.row().classes(row_styles):
            # Username filter
            filters['username_input'] = ui.input(
                'Username',
                placeholder='Search by username...'
            ).props('clearable').classes('w-1/5')

            ui.button('Apply Filters', on_click=lambda: apply_filters()).props(
                'color=primary').classes('w-1/5')
            ui.button('Clear Filters', on_click=lambda: clear_filters()).props(
                'color=secondary flat').classes('w-1/5')

    def filter_users(rows_data):
        """Apply filters to the rows data"""
        filtered = rows_data.copy()

        # Username filter (case-insensitive contains)
        username = filters['username_input'].value
        if username:
            filtered = [r for r in filtered if username.lower()
                        in r['username'].lower()]

        # Role filter
        role = filters['role_input'].value
        if role and role != 'All':
            # Check against the raw role value in the stored user data
            filtered = [r for r in filtered if user_map.get(
                r['id'], {}).get('role') == role]

        # Gender filter
        gender = filters['gender_input'].value
        if gender and gender != 'All':
            filtered = [r for r in filtered if user_map.get(
                r['id'], {}).get('gender') == gender]

        # Education filter
        education = filters['education_input'].value
        if education and education != 'All':
            filtered = [r for r in filtered if user_map.get(
                r['id'], {}).get('education') == education]

        # Status filter
        status = filters['status_input'].value
        if status and status != 'All':
            is_active = status == 'Active'
            filtered = [r for r in filtered if user_map.get(
                r['id'], {}).get('is_active') == is_active]

        # Date range filters
        birth_date_from = filters['birth_date_from'].value
        birth_date_to = filters['birth_date_to'].value
        training_date_from = filters['training_date_from'].value
        training_date_to = filters['training_date_to'].value

        if birth_date_from or birth_date_to:
            filtered = filter_by_date_range(
                filtered, 'birth_date', birth_date_from, birth_date_to)

        if training_date_from or training_date_to:
            filtered = filter_by_date_range(
                filtered, 'training_date', training_date_from, training_date_to)

        # date_type = filters['date_type'].value
        # date_from = filters['date_from'].value
        # date_to = filters['date_to'].value

        # if date_from or date_to:
        #     key = 'birth_date' if date_type == 'Birth Date' else 'training_date'
        #     filtered = filter_by_date_range(filtered, key, date_from, date_to)

        return filtered

    def filter_by_date_range(rows_data, key, date_from, date_to):
        """Filter rows by date range"""
        filtered = []
        for row in rows_data:
            user = user_map.get(row['id'])
            if not user:
                continue

            date_value = user.get(key)
            if not date_value:
                if date_from or date_to:
                    continue
                filtered.append(row)
                continue

            # Ensure date_value is a date object
            if isinstance(date_value, str):
                date_value = datetime.strptime(date_value, DATE_FMT).date()

            if isinstance(date_from, str):
                date_from = datetime.strptime(date_from, DATE_FMT).date()

            if isinstance(date_to, str):
                date_to = datetime.strptime(date_to, DATE_FMT).date()

            if date_from and date_value < date_from:
                continue
            if date_to and date_value > date_to:
                continue

            filtered.append(row)

        return filtered

    def apply_filters():
        """Apply filters and update the table"""
        filtered_rows = filter_users(rows)
        table.rows = filtered_rows
        table.update()

    def clear_filters():
        """Clear all filters and reset the table"""
        filters['username_input'].value = ''
        filters['role_input'].value = 'All'
        filters['gender_input'].value = 'All'
        filters['education_input'].value = 'All'
        filters['status_input'].value = 'All'
        filters['birth_date_from'].value = None
        filters['birth_date_to'].value = None
        filters['training_date_from'].value = None
        filters['training_date_to'].value = None

        table.rows = rows
        table.update()

    # List users table
    with ui.card().classes(STYLES.fullCard):
        ui.label('User List').classes(STYLES.cardTitleLabel)
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
                render_data()
                return

            table.on('row-click', select_row)

            for cell in ['role', 'is_active', 'gender', 'education']:
                table.add_slot(f'body-cell-{cell}', r'''
                    <q-td :props="props"><span v-html="props.value"></span></q-td>
                ''')

    with ui.row().classes('w-full gap-0'):
        # detail edit table
        with ui.card().classes(STYLES.column3Card) as detail_card:
            ui.label('Select a user').classes(STYLES.cardTitleLabel)

            inputs = {}

            def render_detail():

                detail_card.clear()

                with detail_card:
                    ui.label('User Detail').classes(STYLES.cardTitleLabel)
                    # u is the dict from auth.models.User.to_dict
                    u = selected['user']

                    allow_edit_users = user_service.get_user_by_id(
                        id).has_permission('edit_users')
                    is_self = id == u.get('id') if u else False

                    if not u:
                        ui.label('Select a user').classes(STYLES.plainText)
                        return

                    # Not allow edit if not has permission and not the user itself
                    if not any([allow_edit_users, is_self]):
                        ui.label('您既不是管理员也不是本人，因此无权查看和编辑此用户。').classes(
                            STYLES.errorText)
                        return

                    # immutable fields (grey / disabled)
                    with ui.row():
                        ui.input('ID', value=u.get('id')).props(
                            'disable').classes(STYLES.nonEditable)
                        inputs['is_active'] = ui.switch(
                            'Active', value=u.get('is_active'))
                    ui.input('Username', value=u.get('username')).props(
                        'disable').classes(STYLES.nonEditable)
                    ui.input('UUID', value=u.get('uuid')).props(
                        'disable').classes(STYLES.nonEditable + ' w-full')

                    # Role & gender
                    with ui.row().classes('w-full'):
                        inputs['role'] = ui.select(
                            options=list(ROLES),
                            label='Role',
                            value=u.get('role')
                        ).classes('w-1/3')
                        inputs['gender'] = ui.select(
                            options=list(GENDERS),
                            label='Gender',
                            value=u.get('gender')
                        ).classes('w-1/3')

                    # With date handling
                    # Birth
                    birth = u.get('birth_date')
                    inputs['birth_date'] = date_input(
                        'Birth Date', birth.strftime(DATE_FMT))

                    # Training
                    training = u.get('training_date')
                    inputs['training_date'] = date_input(
                        'Training Date', training.strftime(DATE_FMT))

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

                    # Password
                    with ui.expansion('Change Password', icon='lock'):
                        def _v():
                            return inputs['new_password'].value == inputs['confirm_password'].value
                        confirm_password_validation = {
                            k: v for k, v in password_validation.items()}
                        confirm_password_validation.update({
                            '密码不一致': lambda _: _v()
                        })
                        if is_self:
                            ui.label('您正在修改本人的密码，请输入您的当前密码以验证身份。').classes(
                                STYLES.attentionText)
                        else:
                            ui.label('您正在修改他人的密码，请输入您的当前密码以验证身份。').classes(
                                STYLES.attentionText)
                        inputs['password'] = ui.input(
                            'Password', password=True, password_toggle_button=True, validation=password_validation).classes('w-full')
                        inputs['new_password'] = ui.input(
                            'New Password', password=True, password_toggle_button=True, validation=password_validation).classes('w-full')
                        inputs['confirm_password'] = ui.input(
                            'Confirm Password', password=True, password_toggle_button=True, validation=confirm_password_validation).classes('w-full')

                    # Apply
                    def apply():
                        # Check permission again before applying changes
                        # Not allow edit if not has permission and not the user itself
                        if not any([allow_edit_users, is_self]):
                            ui.notify('Permission Deny').classes(
                                'text-red-800')
                            return

                        updated = dict(u)

                        password = inputs['new_password'].value.strip()
                        if password:
                            # If the user is trying to change their own password, check the current password
                            if not user_service.get_user_by_id(id).check_password(inputs['password'].value.strip()):
                                if is_self:
                                    ui.notify('试图修改自己的密码，但当前密码不正确', **
                                              NOTIFY_KWARGS.negative)
                                    return
                                else:
                                    ui.notify('试图修改他人的密码，但当前密码不正确', **
                                              NOTIFY_KWARGS.negative)
                                    return

                            # Check if the new password and confirm password match
                            if not password == inputs['confirm_password'].value.strip():
                                ui.notify('试图修改密码，但两次密码输入不一致', **
                                          NOTIFY_KWARGS.negative)
                                return

                            # Check if the new password meets the validation criteria
                            for k, v in password_validation.items():
                                if not v(password):
                                    ui.notify(
                                        f'试图修改密码，但不符合要求: {k}', **NOTIFY_KWARGS.negative)
                                    return

                            updated['password'] = password

                        keys = ['role', 'gender', 'education',
                                'is_active', 'birth_date', 'training_date']
                        updated.update({k: inputs[k].value for k in keys})

                        trow = table.rows[[r['id']
                                           for r in table.rows].index(u['id'])]
                        for key in keys:
                            trow[key] = updated[key]
                        table.update()

                        if on_edit_apply:
                            on_edit_apply(updated)
                        else:
                            print(f'APPLY, {updated=}')

                        ui.notify('Changes are applied')
                        return

                    ui.button('Apply', on_click=apply).props('color=primary')

                return

        # Data
        with ui.card().classes(STYLES.column3_2Card) as data_card:
            # 标题栏（增加全屏按钮）
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('Experiment Data').classes(STYLES.cardTitleLabel)
                ui.button(icon='fullscreen',
                          on_click=lambda: toggle_fullscreen())

            is_fullscreen = {'value': False}

            def toggle_fullscreen():
                if is_fullscreen['value']:
                    data_card.classes(remove='w-full padding-4')
                    is_fullscreen['value'] = False
                else:
                    data_card.classes(add='w-full padding-4')
                    is_fullscreen['value'] = True
                return

            def render_data():
                data_card.clear()

                with data_card:
                    if not user_service.get_user_by_id(id).has_permission('view_users'):
                        ui.label('Permission Deny').classes(STYLES.errorText)
                        return

                    u = selected['user']
                    if not u:
                        ui.label('Select a user').classes(STYLES.plainText)
                        return

                    # 标题栏（增加全屏按钮）
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label(f'Experiment Data: {u["username"]}').classes(
                            STYLES.cardTitleLabel)
                        ui.button(icon='fullscreen',
                                  on_click=lambda: toggle_fullscreen())

                    # Search for records in ./data/{uuid}/*$exp*/*$dt*/*.csv
                    data_folder = Path(f'./data/{u["uuid"]}')
                    if not data_folder.is_dir():
                        ui.label('No data found').classes(STYLES.errorText)
                        return
                    records = []
                    for experiment_folder in [e for e in data_folder.iterdir() if e.is_dir()]:
                        for time_folder in [e for e in experiment_folder.iterdir() if e.is_dir()]:
                            file = [e for e in time_folder.glob('*.csv')][0]
                            dt = datetime.strptime(
                                time_folder.name, FILE_DATE_FMT)
                            records.append((experiment_folder.name, dt, file))
                    records = pd.DataFrame(
                        records, columns=['experiment', 'datetime', 'file'])

                    # Make table
                    columns = [
                        dict(name='id', label='ID'),
                        dict(name='experiment', label='Experiment'),
                        dict(name='datetime', label='Datetime'),
                    ]

                    [e.update({'field': e['name'], 'sortable': True})
                     for e in columns]

                    rows = [{'id': i, 'experiment': row['experiment'], 'datetime': row['datetime'].isoformat()}
                            for i, row in records.iterrows()]

                    with ui.table(
                        rows=rows,
                        columns=columns,
                        row_key='id',
                        pagination={'rowsPerPage': 10},
                    ).classes('w-full').props('dense bordered flat') as table:
                        def select_row(e):
                            selected_row = e.args[1]
                            row = records.iloc[selected_row['id']]
                            df = pd.read_csv(row['file'])
                            record_card.clear()
                            with record_card:
                                ui.label(f'Record Preview: {row["experiment"]} | {row["datetime"].isoformat()}').classes(
                                    STYLES.cardTitleLabel)
                                ui.table.from_pandas(df).classes('w-full')
                            return

                        table.on('row-click', select_row)
                        pass

                    record_card = ui.card().classes('w-full mt-4')
                    with record_card:
                        ui.label('Record Preview [Select a row]').classes(
                            STYLES.cardTitleLabel)

                return

    return
