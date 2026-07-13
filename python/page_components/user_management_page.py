import asyncio
import os
import sys
import subprocess
import pandas as pd

from loguru import logger
from nicegui import ui
from pathlib import Path
from datetime import datetime

from .inputs import date_input, image_select, image_table_txt_select

sys.path.append('..')  # noqa
from constants import *
from auth.user_service import UserService, User, or_

# ------------------------------------------------------------------------------
logger.add("log/user_managerment_{time:YYYY-MM-DD}.log",
           encoding=ENCODING, rotation='1 day')


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

    def reload_rows_and_user_map():
        rows.clear()
        user_map.clear()

        users = sorted([e.to_dict()
                        for e in user_service.list_users()], key=lambda e: e['id'])

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

    reload_rows_and_user_map()

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
                value='All',
                on_change=lambda: apply_filters()
            ).classes('w-1/5')

            # Gender filter
            filters['gender_input'] = ui.select(
                options=['All'] + list(GENDERS),
                label='Gender',
                value='All',
                on_change=lambda: apply_filters()
            ).classes('w-1/5')

            # Education filter
            filters['education_input'] = ui.select(
                options=['All'] + list(EDUCATIONS),
                label='Education',
                value='All',
                on_change=lambda: apply_filters()
            ).classes('w-1/5')

            # Status filter
            filters['status_input'] = ui.select(
                options=['All', 'Active', 'Inactive'],
                label='Status',
                value='All',
                on_change=lambda: apply_filters()
            ).classes('w-1/5')

        with ui.row().classes(row_styles):
            # with ui.column().classes('gap-2'):
            filters['birth_date_from'] = date_input(
                'Birth date from', None).classes('w-1/5').on_value_change(lambda: apply_filters())
            filters['birth_date_to'] = date_input(
                'Birth date to', None).classes('w-1/5').on_value_change(lambda: apply_filters())

            # with ui.column().classes('gap-2'):
            filters['training_date_from'] = date_input(
                'Training date from', None).classes('w-1/5').on_value_change(lambda: apply_filters())
            filters['training_date_to'] = date_input(
                'Training date to', None).classes('w-1/5').on_value_change(lambda: apply_filters())

        # Action buttons
        with ui.row().classes(row_styles):
            # Username filter
            filters['username_input'] = ui.input(
                'Username',
                placeholder='Search by username...',
                on_change=lambda: apply_filters()
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
        reload_rows_and_user_map()
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

        reload_rows_and_user_map()
        table.rows = rows
        table.update()

    # List users table
    with ui.card().classes(STYLES.fullCard):

        with ui.row().classes('w-full'):
            def _on_click_refresh_user_list():
                reload_rows_and_user_map()
                table.rows = rows
                table.update()

            def _on_click_export_users():
                print('export_users')
                if not user_service.get_user_by_id(id).has_permission('export_users'):
                    ui.notify('您目前没有 export_users 权限或账户不可用，不允许进行此操作',
                              **NOTIFY_KWARGS.negative)
                rows = table.rows
                selected_ids = [e['id'] for e in rows]
                db_users = user_service.session.query(
                    User).filter(User.id.in_(selected_ids)).all()

                print(selected_ids)
                print(db_users)
                columns = [c.name for c in User.__table__.columns]
                print(columns)
                # Convert to pandas DataFrame
                df = pd.DataFrame([user.__dict__ for user in db_users])

                # Remove SQLAlchemy internal '_sa_instance_state' column if present
                df = df.drop(columns=['_sa_instance_state'], errors='ignore')

                # Save to CSV
                filename = Path('./export/users_export.csv')
                filename.parent.mkdir(exist_ok=True, parents=True)
                df.to_csv(filename, index=False, encoding='utf-8')

                content = f'Export users db into {filename}'
                ui.notify(content, **NOTIFY_KWARGS.positive)
                logger.info(content)

                return df

            ui.label('User List').classes(STYLES.cardTitleLabel)
            ui.space()
            ui.button('刷新用户列表', on_click=_on_click_refresh_user_list)

            # 当拥有 export_users 权限时，添加导出用户信息按钮
            if user_service.get_user_by_id(id).has_permission('export_users'):
                ui.button('导出用户信息', on_click=_on_click_export_users)
                pass

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

    # Change User Profile
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
                        ui.label('您既没有 edit_users 权限也不是本人，因此无权查看和编辑此用户。').classes(
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
                            k: v for k, v in PASSWORD_VALIDATION.items()}
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
                            'Password', password=True, password_toggle_button=True, validation=PASSWORD_VALIDATION).classes('w-full')
                        inputs['new_password'] = ui.input(
                            'New Password', password=True, password_toggle_button=True, validation=PASSWORD_VALIDATION).classes('w-full')
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
                            for k, v in PASSWORD_VALIDATION.items():
                                if not v(password):
                                    ui.notify(
                                        f'试图修改密码，但不符合要求: {k}', **NOTIFY_KWARGS.negative)
                                    return

                            updated['password'] = password

                        keys = ['role', 'gender', 'education',
                                'is_active', 'birth_date', 'training_date']
                        updated.update({k: inputs[k].value for k in keys})

                        if on_edit_apply:
                            on_edit_apply(updated)
                        else:
                            print(f'APPLY, {updated=}')

                        reload_rows_and_user_map()
                        table.rows = rows
                        table.update()

                        ui.notify('Changes are applied')
                        return

                    ui.button('Apply', on_click=apply).props('color=primary')

                return

        # Experiment Data
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
                            if not (time_folder / 'experiment.finish').exists():
                                continue
                            file = next(time_folder.glob('*.csv'))
                            dt = datetime.strptime(
                                time_folder.name[:4+4+1+6], FILE_DATE_FMT)
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

                            experiment_name = row['experiment']
                            experiment_datetime = row['datetime'].isoformat()
                            eeg_data_folder = row['file'].parent

                            # --------------------------------------------------
                            record_card.clear()
                            with record_card:
                                ui.label(f'Record Preview: {experiment_name} | {experiment_datetime}').classes(
                                    STYLES.cardTitleLabel)
                                ui.table.from_pandas(df).classes(
                                    STYLES.pandasTable)

                            # --------------------------------------------------
                            eeg_card.clear()
                            with eeg_card:
                                fill_eeg_card(
                                    experiment_name, experiment_datetime, eeg_data_folder)

                            return

                        table.on('row-click', select_row)
                        pass

                    record_card = ui.card().classes('w-full mt-4')
                    with record_card:
                        ui.label('Record Preview [Select a row]').classes(
                            STYLES.cardTitleLabel)

                return

    # EEG Data
    with ui.row().classes('w-full gap-0'):
        with ui.card().classes(STYLES.fullCard):
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('EEG Data').classes(STYLES.cardTitleLabel)
                with ui.card().classes('w-full') as eeg_card:
                    pass

    return


def fill_eeg_card(experiment_name: str, experiment_datetime: str, eeg_data_folder: Path):
    '''
    Fill and render the EEG processing card
    '''

    ui.label(f'Record Preview: {experiment_name} | {experiment_datetime}').classes(
        STYLES.cardTitleLabel)

    # ----------------------------------------------
    with ui.expansion(f'数据所在目录: {eeg_data_folder.as_posix()}').classes('w-full'):
        files = sorted([e.relative_to(eeg_data_folder)
                        for e in eeg_data_folder.rglob('*')])
        df_files = pd.DataFrame(
            files, columns=['文件'])
        ui.table.from_pandas(df_files).classes(
            'w-full max-h-[28em]')

    # ----------------------------------------------
    script_folder = Path('./preprocessing/script')
    script_files = sorted(script_folder.rglob(f'{experiment_name}_*.py'))
    methods = {
        e.name.split('_')[-1][:-3]: e for e in script_files
    }

    ui.separator()
    with ui.expansion('数据预处理', value=True).classes('w-full'):
        if 'preprocessing' in methods:
            with ui.card().classes('w-full'):
                script = methods['preprocessing']
                options = ['c 滤波', 'd 波形图呈现', 'e 脑地形图呈现',
                           'f 坏道检测与插值', 'g ICA去噪', 'h 分段提取和噪音试次检测剔除']

                with ui.row().classes('w-full'):
                    ui.label('1. 预处理')
                    ui.space()
                    ui.label(f'脚本：{script.as_posix()}')

                with ui.row().classes('w-full'):
                    selected_preprocessing = [e for e in options]  # 存储选中的值

                    cwd = eeg_data_folder.as_posix()
                    preprocessing_options = ['--cnt', 'experiment-raw.cnt',
                                             '--out', 'preprocessing']
                    preprocessing_options_2 = []

                    # 创建多个 checkbox
                    checkboxes = []
                    for opt in options:
                        cb = ui.checkbox(opt, value=True)  # 标准方框
                        checkboxes.append(cb)

                        # 监听变化，更新选中列表
                        def update_selection(cb=cb, opt=opt):
                            if cb.value:
                                if opt not in selected_preprocessing:
                                    selected_preprocessing.append(opt)
                            else:
                                if opt in selected_preprocessing:
                                    selected_preprocessing.remove(opt)

                            while preprocessing_options_2:
                                preprocessing_options_2.pop()
                            args = [
                                f'--no-{e[0]}' for e in options if e not in selected_preprocessing]
                            [preprocessing_options_2.append(e) for e in args]
                            preprocessing_commands_label.text = ' '.join(
                                preprocessing_options + preprocessing_options_2)

                        cb.on_value_change(update_selection)

                ui.button('开始预处理',
                          on_click=lambda evt,
                          options1=preprocessing_options,
                          options2=preprocessing_options_2: preprocessing(
                              evt, eeg_data_folder, options1, options2, script=script, on_finish=render_preprocessing_results))
                ui.label(f'{cwd=}')
                preprocessing_commands_label = ui.label(
                    ' '.join(preprocessing_options + preprocessing_options_2)).classes('w-full')
        else:
            ui.label('没有找到预处理脚本').classes(STYLES.errorText)

        # ----------------------------------------------------------------------
        # Results of preprocessing
        preprocessing_results_card = ui.card().classes('w-full')

        def render_preprocessing_results():
            preprocessing_folder = eeg_data_folder / 'preprocessing'
            preprocessing_results_card.clear()
            with preprocessing_results_card:
                ui.label('预处理结果')

                if preprocessing_folder.with_name('preprocessing.finish').exists():
                    ui.textarea(
                        label='preprocessing.stdout',
                        value=open(preprocessing_folder.with_name('preprocessing.stdout'), encoding=ENCODING).read()).classes('w-full')
                    _image_files = sorted(preprocessing_folder.rglob('*.png'))
                    image_files = {e.absolute(): e.relative_to(
                        preprocessing_folder).as_posix() for e in _image_files}
                    image_select(image_files)

                elif preprocessing_folder.with_name('preprocessing.stderr').is_file():
                    ui.textarea(
                        label='preprocessing.stderr',
                        value=open(preprocessing_folder.with_name('preprocessing.stderr'), encoding=ENCODING).read()).classes('w-full')
                    ui.label('没有找到预处理结果').classes(STYLES.errorText)

                else:
                    ui.label('没有找到预处理结果').classes(STYLES.errorText)

                ui.button('点击此处刷新结果', on_click=render_preprocessing_results)

        render_preprocessing_results()

    ui.separator()
    with ui.expansion('特征分析', value=True).classes('w-full'):
        processing_methods = [e for e in methods if e != 'preprocessing']

        if len(processing_methods) == 0:
            ui.label(f'2.没有找到特征分析脚本').classes(STYLES.errorText)
            return

        _clean_epo = eeg_data_folder / 'preprocessing' / 'clean_epo.fif'
        _preprocessing_finish = eeg_data_folder / 'preprocessing.finish'

        if not all([_clean_epo.is_file(), _preprocessing_finish.is_file()]):
            ui.label(f'2.预处理未完成，请先完成预处理再进行特征分析').classes(STYLES.errorText)
            return

        ui.label(f'数据目录：{_clean_epo}')

        with ui.row().classes('items-center'):
            ui.label(f'请选择特征分析方法').classes(STYLES.infoText)
            select_processing_method = ui.select(
                processing_methods, value=processing_methods[0])

        processing_card = ui.card().classes(STYLES.fullCard)

        class Processing:
            def __init__(self):
                select_processing_method.on_value_change(
                    self._on_select_processing_method)
                self._on_select_processing_method()

            def _on_select_processing_method(self):
                processing_card.clear()
                _selected_method = select_processing_method.value
                _script = methods[_selected_method]
                _processing_folder = eeg_data_folder / _selected_method
                with processing_card:
                    ui.label(f'特征分析：{_selected_method}').classes(
                        STYLES.infoText)
                    ui.label(f'特征分析脚本：{_script}').classes(STYLES.infoText)
                    ui.label(f'特征分析目录：{_processing_folder}').classes(
                        STYLES.infoText)

                    result_card = ui.card().classes('w-full')

                    def _on_finish():
                        files = sorted(
                            [e for e in _processing_folder.rglob('*') if e.is_file()])
                        if len(files) == 0:
                            return

                        _files = {e: e.relative_to(
                            _processing_folder).as_posix() for e in files}
                        result_card.clear()
                        with result_card:
                            ui.label('特征分析结果')
                            # ui.select(img_files, value=img_files[0])
                            image_table_txt_select(_files)

                    _on_finish()

                    commands = [
                        'python', _script.absolute().as_posix(),
                        '--epo', _clean_epo.absolute().as_posix(),
                        '--out', '.'
                    ]
                    ui.button('开始特征分析', on_click=lambda e: feature_processing(
                        e, _processing_folder, commands, _selected_method, _on_finish))

        processing = Processing()

        pass

    return


async def feature_processing(event, cwd: Path, commands: list, mname: str, on_finish):
    '''
    mname: method name.
    '''

    # print(event, cwd, commands, mname)
    ui.notify(f'开始特征分析：{commands} in {cwd}', **NOTIFY_KWARGS.positive)
    await asyncio.sleep(0.1)

    cwd.mkdir(exist_ok=True, parents=True)

    # Delete existing files
    _finish = cwd / f'{mname}.finish'
    if _finish.is_file():
        _finish.unlink()

    _error = cwd / f'{mname}.error'
    if _error.is_file():
        _error.unlink()

    # Actually running the experiment
    _stdout = open(cwd / f'{mname}.stdout', 'w', encoding=ENCODING)
    _stderr = open(cwd / f'{mname}.stderr', 'w', encoding=ENCODING)
    try:
        completed = subprocess.run(
            commands, cwd=cwd, stdout=_stdout, stderr=_stderr, encoding=ENCODING,
            env={**os.environ, 'PYTHONIOENCODING': ENCODING}  # 设置 Python 环境变量
        )
        assert completed.returncode == 0, '执行完毕但 returncode 不为 0。'
        print(completed, file=open(_finish, 'w', encoding=ENCODING))
        logger.info(f'{mname} finished: {commands=}')

    except Exception as err:
        logger.error(f'{mname} failed: {err=}')
        with open(_error, 'w', encoding=ENCODING) as file:
            file.write(f'{err=}\r\n')
            import traceback
            file.write(traceback.format_exc())
        ui.notify(f'特征分析（{mname}）中遇到错误：{err=}', **NOTIFY_KWARGS.negative)

    on_finish()
    return


async def preprocessing(event, cwd: Path, options1, options2, script: Path, on_finish):
    print(event, cwd, options1, options2)
    commands = [
        'python', script.absolute().as_posix(),
    ] + options1 + options2

    (cwd / 'preprocessing').mkdir(exist_ok=True, parents=True)

    # Delete existing files
    _finish = cwd / 'preprocessing.finish'
    if _finish.is_file():
        _finish.unlink()

    _error = cwd / 'preprocessing.error'
    if _error.is_file():
        _error.unlink()

    # Actually running the experiment
    _stdout = open(cwd / 'preprocessing.stdout', 'w', encoding=ENCODING)
    _stderr = open(cwd / 'preprocessing.stderr', 'w', encoding=ENCODING)
    try:
        # completed = subprocess.run(
        #     commands, cwd=cwd, stdout=_stdout, stderr=_stderr, encoding=ENCODING,
        #     env={**os.environ, 'PYTHONIOENCODING': ENCODING}  # 设置 Python 环境变量
        # )
        # assert completed.returncode == 0, '执行完毕但 returncode 不为 0。'
        # print(completed, file=open(_finish, 'w', encoding=ENCODING))
        ui.notify(f'预处理开始：{commands=}', **NOTIFY_KWARGS.positive)
        await asyncio.sleep(0.1)

        # 在线程池中运行同步的 subprocess.run
        result = await asyncio.to_thread(
            subprocess.run,
            commands,
            cwd=cwd,
            stdout=_stdout,
            stderr=_stderr,
            encoding=ENCODING,
            env={**os.environ, 'PYTHONIOENCODING': ENCODING}
        )

        # 等待进程完成
        assert result.returncode == 0, '执行完毕但 returncode 不为 0。'
        print(result, file=open(_finish, 'w', encoding=ENCODING))

        logger.info(f'Preprocessing finished: {commands=}')
        ui.notify(f'预处理完成：{commands=}', **NOTIFY_KWARGS.positive)
        await asyncio.sleep(0.1)

    except Exception as err:
        logger.exception(err)
        logger.error(f'Preprocessing failed: {err=}')
        with open(_error, 'w', encoding=ENCODING) as file:
            file.write(f'{err=}\r\n')
            import traceback
            file.write(traceback.format_exc())
        ui.notify(f'预处理过程中遇到错误：{err=}', **NOTIFY_KWARGS.negative)

    await asyncio.sleep(0.1)
    on_finish()
    await asyncio.sleep(0.1)

    return
