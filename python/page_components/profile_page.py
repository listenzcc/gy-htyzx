from nicegui import ui
from datetime import datetime


def profile_content_readonly(dct: dict):
    # Create a nicely styled table
    with ui.card().classes('w-full mx-auto p-6'):
        ui.label('用户信息').classes('text-xl font-semibold mb-4')

        # Define field labels and formatting
        fields = [
            ('用户名', 'username'),
            ('用户ID', 'id'),
            ('用户UUID', 'uuid'),
            ('本次登陆的SessionID', 'session_id'),
            ('角色', 'role'),
            ('激活状态', 'is_active'),
            ('性别', 'gender'),
            ('出生日期', 'birth_date'),
            ('教育背景', 'education'),
            ('培训日期', 'training_date'),
            ('创建时间', 'created_at'),
            ('最后登录时间', 'last_login'),
        ]

        # Create table
        with ui.table(rows=[], columns=[
            {'name': 'field', 'label': '项', 'field': 'field', 'sortable': True},
            {'name': 'value', 'label': '值', 'field': 'value', 'sortable': True},
        ]).classes('w-full').props('dense bordered flat') as table:

            # Build rows
            rows = []
            for label, key in fields:
                value = dct.get(key)

                # Format datetime objects
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, bool):
                    value = '✓ 激活' if value else '✗ 未激活'
                elif value == '':
                    value = '未提供'

                rows.append({'field': label, 'value': value})

            table.rows = rows
