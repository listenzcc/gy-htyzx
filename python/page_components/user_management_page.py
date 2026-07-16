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
        'usernames_of_interest': None
    }

    columns = [
        dict(name='id', label='ID'),
        dict(name='username', label='用户名'),
        dict(name='role', label='角色'),
        dict(name='gender', label='性别'),
        dict(name='birth_date', label='出生日期'),
        dict(name='training_date', label='参训日期'),
        dict(name='education', label='学历'),
        dict(name='is_active', label='激活状态'),
        dict(name='created_at', label='账号创建时间'),
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
    with ui.expansion('展开/关闭过滤器', icon='menu').classes('w-full'):
        # .classes('text-lg font-bold mb-2')
        # ui.label('Filters').classes(STYLES.cardTitleLabel)

        row_styles = 'w-full gap-4 justify-center items-center'
        with ui.row().classes(row_styles):
            filters['usernames_of_interest'] = ui.textarea(
                label='用户花名册（只对这些用户进行管理，用户名严格匹配，用【空格】隔开）',
                placeholder='请输入用户花名册',
                on_change=lambda: apply_filters()
            ).classes('w-full')

        with ui.row().classes(row_styles):
            # Role filter
            filters['role_input'] = ui.select(
                options=['不限'] + list(ROLES),
                label='角色',
                value='不限',
                on_change=lambda: apply_filters()
            ).classes('w-1/5')

            # Gender filter
            filters['gender_input'] = ui.select(
                options=['不限'] + list(GENDERS),
                label='性别',
                value='不限',
                on_change=lambda: apply_filters()
            ).classes('w-1/5')

            # Education filter
            filters['education_input'] = ui.select(
                options=['不限'] + list(EDUCATIONS),
                label='学历',
                value=None,
                with_input=True,
                new_value_mode='add-unique',
                on_change=lambda: apply_filters()
            ).classes('w-1/5')

            # Status filter
            filters['status_input'] = ui.select(
                options=['不限', 'Active', 'Inactive'],
                label='激活状态',
                value='不限',
                on_change=lambda: apply_filters()
            ).classes('w-1/5')

        with ui.row().classes(row_styles):
            # with ui.column().classes('gap-2'):
            filters['birth_date_from'] = date_input(
                '出生日期（最早）', None).classes('w-1/5').on_value_change(lambda: apply_filters())
            filters['birth_date_to'] = date_input(
                '出生日期（最晚）', None).classes('w-1/5').on_value_change(lambda: apply_filters())

            # with ui.column().classes('gap-2'):
            filters['training_date_from'] = date_input(
                '参训日期（最早）', None).classes('w-1/5').on_value_change(lambda: apply_filters())
            filters['training_date_to'] = date_input(
                '参训日期（最晚）', None).classes('w-1/5').on_value_change(lambda: apply_filters())

        # Action buttons
        with ui.row().classes(row_styles):
            # Username filter
            filters['username_input'] = ui.input(
                '用户名',
                placeholder='用户名包含此字符串',
                on_change=lambda: apply_filters()
            ).props('clearable').classes('w-1/5')

            ui.button('应用过滤条件', on_click=lambda: apply_filters()).props(
                'color=primary').classes('w-1/5')
            ui.button('清除过滤条件', on_click=lambda: clear_filters()).props(
                'color=secondary flat').classes('w-1/5')

    def filter_users(rows_data):
        """Apply filters to the rows data"""
        filtered = rows_data.copy()

        # Filter based on usernames_of_interest
        usernames_of_interest = [e.strip(
        ) for e in filters['usernames_of_interest'].value.strip().split(' ') if e.strip()]
        if usernames_of_interest:
            filtered = [r for r in filtered if r['username']
                        in usernames_of_interest]

        # Username filter (case-insensitive contains)
        username = filters['username_input'].value.strip()
        if username:
            filtered = [r for r in filtered if username.lower()
                        in r['username'].lower()]

        # Role filter
        role = filters['role_input'].value
        if role and role != '不限':
            # Check against the raw role value in the stored user data
            filtered = [r for r in filtered if user_map.get(
                r['id'], {}).get('role') == role]

        # Gender filter
        gender = filters['gender_input'].value
        if gender and gender != '不限':
            filtered = [r for r in filtered if user_map.get(
                r['id'], {}).get('gender') == gender]

        # Education filter
        education = filters['education_input'].value
        if education and education != '不限':
            filtered = [r for r in filtered if user_map.get(
                r['id'], {}).get('education') == education]

        # Status filter
        status = filters['status_input'].value
        if status and status != '不限':
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
        filters['usernames_of_interest'].value = ''
        filters['username_input'].value = ''
        filters['role_input'].value = '不限'
        filters['gender_input'].value = '不限'
        filters['education_input'].value = '不限'
        filters['status_input'].value = '不限'
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
                df.to_csv(filename, index=False, encoding='gbk')

                content = f'Export users db into {filename}'
                ui.notify(content, **NOTIFY_KWARGS.positive)
                logger.info(content)

                return df

            ui.label('用户列表').classes(STYLES.cardTitleLabel)
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
                return

            table.on('row-click', select_row)

            for cell in ['role', 'is_active', 'gender', 'education']:
                table.add_slot(f'body-cell-{cell}', r'''
                    <q-td :props="props"><span v-html="props.value"></span></q-td>
                ''')

    # Change User Profile
    with ui.row().classes('w-full'):
        # detail edit table
        with ui.card().classes(STYLES.fullCard) as detail_card:
            ui.label('【尚未选择用户】').classes(STYLES.cardTitleLabel)

            inputs = {}

            def render_detail():

                detail_card.clear()

                with detail_card:
                    ui.label('待修改的用户信息').classes(STYLES.cardTitleLabel)
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
                    with ui.row().classes('justify-evenly w-full'):
                        ui.input('ID', value=u.get('id')).props(
                            'disable').classes(STYLES.nonEditable)
                        ui.input('用户名', value=u.get('username')).props(
                            'disable').classes(STYLES.nonEditable)
                        ui.input('UUID', value=u.get('uuid')).props(
                            'disable').classes(STYLES.nonEditable + ' w-1/3')
                        inputs['is_active'] = ui.switch(
                            '激活状态', value=u.get('is_active'))

                    # Role & gender
                    with ui.row().classes('justify-evenly w-full'):
                        with ui.column().classes('w-1/3'):
                            inputs['role'] = ui.select(
                                options=list(ROLES),
                                label='角色',
                                value=u.get('role')
                            ).classes('w-full')

                            inputs['gender'] = ui.select(
                                options=list(GENDERS),
                                label='性别',
                                value=u.get('gender')
                            ).classes('w-full')

                            # Education
                            education = u.get('education')
                            options = [e for e in EDUCATIONS]
                            if not education in options:
                                options.append(education)
                            inputs['education'] = ui.select(
                                options=options,
                                value=education,
                                label='学历',
                                new_value_mode='add'
                            ).classes('w-full')

                            # With date handling
                            # Birth
                            birth = u.get('birth_date')
                            inputs['birth_date'] = date_input(
                                '出生日期', birth.strftime(DATE_FMT)).classes('w-full')

                            # Training
                            training = u.get('training_date')
                            inputs['training_date'] = date_input(
                                '参训日期', training.strftime(DATE_FMT)).classes('w-full')

                        with ui.column().classes('w-1/3'):
                            # Password
                            with ui.expansion('修改密码', icon='lock'):
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
                                    '密码', password=True, password_toggle_button=True, validation=PASSWORD_VALIDATION).classes('w-full')
                                inputs['new_password'] = ui.input(
                                    '新密码', password=True, password_toggle_button=True, validation=PASSWORD_VALIDATION).classes('w-full')
                                inputs['confirm_password'] = ui.input(
                                    '确认新密码', password=True, password_toggle_button=True, validation=confirm_password_validation).classes('w-full')

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

                    with ui.row().classes('justify-evenly w-full'):
                        ui.button('应用修改', on_click=apply).props(
                            'color=primary')

                return
