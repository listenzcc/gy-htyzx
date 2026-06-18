import sqlite3
import hashlib
from datetime import datetime
from nicegui import ui
import pandas as pd
import os

# 数据库初始化
DB_NAME = 'user_management.db'


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            birth_date TEXT,
            education TEXT,
            gender TEXT,
            training_date TEXT,
            role TEXT DEFAULT 'user',
            created_at TEXT
        )
    ''')
    # 创建默认管理员账户
    admin_exists = c.execute(
        "SELECT * FROM users WHERE name='admin'").fetchone()
    if not admin_exists:
        hashed_pwd = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute('''
            INSERT INTO users (name, password, birth_date, education, gender, training_date, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', hashed_pwd, '1990-01-01', '本科', '男', '2026-01-01', 'admin', datetime.now().isoformat()))
    conn.commit()
    conn.close()


init_db()

# 数据库操作函数


def get_db_connection():
    return sqlite3.connect(DB_NAME)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# 全局变量存储当前用户
current_user = None
current_role = None
main_content = None


def logout():
    global current_user, current_role
    current_user = None
    current_role = None
    ui.notify('已退出', type='info')
    show_main_content()


def show_register():
    with ui.dialog() as dialog, ui.card():
        ui.label('用户注册').classes('text-h5')
        name = ui.input('姓名')
        password = ui.input('密码', password=True)
        confirm_pwd = ui.input('确认密码', password=True)
        birth_date = ui.input('出生年月', placeholder='YYYY-MM-DD')
        education = ui.select('学历', ['高中', '大专', '本科', '硕士', '博士'])
        gender = ui.select('性别', ['男', '女'])
        training_date = ui.input('受训时间', placeholder='YYYY-MM-DD')

        def do_register():
            if password.value != confirm_pwd.value:
                ui.notify('密码不一致', type='negative')
                return
            try:
                conn = get_db_connection()
                c = conn.cursor()
                hashed_pwd = hash_password(password.value)
                c.execute('''
                    INSERT INTO users (name, password, birth_date, education, gender, training_date, role, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name.value, hashed_pwd, birth_date.value, education.value,
                      gender.value, training_date.value, 'user', datetime.now().isoformat()))
                conn.commit()
                conn.close()
                ui.notify(f'用户 {name.value} 注册成功', type='positive')
                dialog.close()
            except sqlite3.IntegrityError:
                ui.notify('用户名已存在', type='negative')

        with ui.row():
            ui.button('注册', on_click=do_register).classes(
                'bg-blue-500 text-white')
            ui.button('取消', on_click=dialog.close)
    dialog.open()


def show_login():
    with ui.dialog() as dialog, ui.card():
        ui.label('用户登录').classes('text-h5')
        name = ui.input('姓名')
        password = ui.input('密码', password=True)

        def do_login():
            global current_user, current_role
            conn = get_db_connection()
            c = conn.cursor()
            user = c.execute('SELECT * FROM users WHERE name=? AND password=?',
                             (name.value, hash_password(password.value))).fetchone()
            conn.close()
            if user:
                current_user = user[1]
                current_role = user[7]
                ui.notify(f'欢迎 {current_user}', type='positive')
                dialog.close()
                show_main_content()
            else:
                ui.notify('用户名或密码错误', type='negative')

        with ui.row():
            ui.button('登录', on_click=do_login).classes(
                'bg-green-500 text-white')
            ui.button('取消', on_click=dialog.close)
    dialog.open()


def show_user_management():
    if current_role != 'admin':
        ui.notify('权限不足', type='negative')
        return

    with ui.dialog() as dialog, ui.card().classes('w-3/4'):
        ui.label('用户管理').classes('text-h5')
        users_table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id'},
                {'name': 'name', 'label': '姓名', 'field': 'name'},
                {'name': 'birth_date', 'label': '出生年月', 'field': 'birth_date'},
                {'name': 'education', 'label': '学历', 'field': 'education'},
                {'name': 'gender', 'label': '性别', 'field': 'gender'},
                {'name': 'training_date', 'label': '受训时间', 'field': 'training_date'},
                {'name': 'role', 'label': '角色', 'field': 'role'},
            ],
            rows=[]
        )

        def refresh_users():
            conn = get_db_connection()
            c = conn.cursor()
            rows = c.execute(
                'SELECT id, name, birth_date, education, gender, training_date, role FROM users').fetchall()
            conn.close()
            users_table.rows = [dict(zip(
                ['id', 'name', 'birth_date', 'education', 'gender', 'training_date', 'role'], row)) for row in rows]
            users_table.update()

        refresh_users()

        # 修改用户信息
        ui.label('修改用户信息').classes('text-h6 mt-4')
        user_id = ui.input('要修改的用户ID', placeholder='输入数字ID')

        ui.label('要修改的字段').classes('text-h6 mt-4')
        field = ui.select(
            options=['name', 'birth_date', 'education', 'gender', 'training_date', 'role'])
        new_value = ui.input('新值')

        def update_user():
            if not user_id.value:
                ui.notify('请输入用户ID', type='negative')
                return
            try:
                user_id_int = int(user_id.value)
            except ValueError:
                ui.notify('用户ID必须是数字', type='negative')
                return

            conn = get_db_connection()
            c = conn.cursor()
            try:
                if field.value == 'role':
                    if new_value.value not in ['user', 'admin']:
                        ui.notify('角色只能为 user 或 admin', type='negative')
                        return
                c.execute(
                    f'UPDATE users SET {field.value}=? WHERE id=?', (new_value.value, user_id_int))
                conn.commit()
                ui.notify('修改成功', type='positive')
                refresh_users()
            except Exception as e:
                ui.notify(f'修改失败: {str(e)}', type='negative')
            finally:
                conn.close()

        # 删除用户
        ui.label('删除用户').classes('text-h6 mt-4')
        del_id = ui.input('要删除的用户ID', placeholder='输入数字ID')

        def delete_user():
            if not del_id.value:
                ui.notify('请输入用户ID', type='negative')
                return
            try:
                del_id_int = int(del_id.value)
            except ValueError:
                ui.notify('用户ID必须是数字', type='negative')
                return

            if del_id_int == 1:
                ui.notify('不能删除管理员账户', type='negative')
                return
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('DELETE FROM users WHERE id=?', (del_id_int,))
            conn.commit()
            conn.close()
            ui.notify('删除成功', type='positive')
            refresh_users()

        # 修改用户密码
        ui.label('修改用户密码').classes('text-h6 mt-4')
        pwd_user_id = ui.input('用户ID', placeholder='输入数字ID')
        new_pwd = ui.input('新密码', password=True)

        def change_password():
            if not pwd_user_id.value or not new_pwd.value:
                ui.notify('请输入完整信息', type='negative')
                return
            try:
                pwd_user_id_int = int(pwd_user_id.value)
            except ValueError:
                ui.notify('用户ID必须是数字', type='negative')
                return

            conn = get_db_connection()
            c = conn.cursor()
            c.execute('UPDATE users SET password=? WHERE id=?',
                      (hash_password(new_pwd.value), pwd_user_id_int))
            conn.commit()
            conn.close()
            ui.notify('密码修改成功', type='positive')
            refresh_users()

        with ui.row():
            ui.button('修改信息', on_click=update_user).classes(
                'bg-blue-500 text-white')
            ui.button('删除用户', on_click=delete_user).classes(
                'bg-red-500 text-white')
            ui.button('修改密码', on_click=change_password).classes(
                'bg-orange-500 text-white')
            ui.button('刷新', on_click=refresh_users)
            ui.button('关闭', on_click=dialog.close)
    dialog.open()


def show_user_profile():
    global current_user
    conn = get_db_connection()
    c = conn.cursor()
    user = c.execute(
        'SELECT name, birth_date, education, gender, training_date FROM users WHERE name=?', (current_user,)).fetchone()
    conn.close()

    with ui.dialog() as dialog, ui.card():
        ui.label('个人信息').classes('text-h5')
        ui.label(f'姓名: {user[0]}')
        birth_date = ui.input('出生年月', value=user[1])
        education = ui.select(
            '学历', ['高中', '大专', '本科', '硕士', '博士'], value=user[2])
        gender = ui.select('性别', ['男', '女'], value=user[3])
        training_date = ui.input('受训时间', value=user[4])

        def update_profile():
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                UPDATE users SET birth_date=?, education=?, gender=?, training_date=?
                WHERE name=?
            ''', (birth_date.value, education.value, gender.value, training_date.value, current_user))
            conn.commit()
            conn.close()
            ui.notify('信息更新成功', type='positive')
            dialog.close()

        with ui.row():
            ui.button('更新', on_click=update_profile).classes(
                'bg-blue-500 text-white')
            ui.button('关闭', on_click=dialog.close)
    dialog.open()


def show_filter_users():
    if current_role != 'admin':
        ui.notify('权限不足', type='negative')
        return

    with ui.dialog() as dialog, ui.card().classes('w-3/4'):
        ui.label('高级筛选').classes('text-h5')

        filter_type = ui.select(
            '筛选类别', ['education', 'gender', 'training_date'])
        filter_value = ui.input('筛选值')

        result_table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id'},
                {'name': 'name', 'label': '姓名', 'field': 'name'},
                {'name': 'birth_date', 'label': '出生年月', 'field': 'birth_date'},
                {'name': 'education', 'label': '学历', 'field': 'education'},
                {'name': 'gender', 'label': '性别', 'field': 'gender'},
                {'name': 'training_date', 'label': '受训时间', 'field': 'training_date'},
            ],
            rows=[]
        )

        def do_filter():
            if not filter_value.value:
                ui.notify('请输入筛选值', type='negative')
                return
            conn = get_db_connection()
            c = conn.cursor()
            query = f'SELECT id, name, birth_date, education, gender, training_date FROM users WHERE {filter_type.value} LIKE ?'
            rows = c.execute(query, (f'%{filter_value.value}%',)).fetchall()
            conn.close()
            result_table.rows = [dict(zip(
                ['id', 'name', 'birth_date', 'education', 'gender', 'training_date'], row)) for row in rows]
            result_table.update()
            ui.notify(f'找到 {len(rows)} 条记录', type='info')

        with ui.row():
            ui.button('筛选', on_click=do_filter).classes(
                'bg-blue-500 text-white')
            ui.button('关闭', on_click=dialog.close)
    dialog.open()


def show_import_users():
    if current_role != 'admin':
        ui.notify('权限不足', type='negative')
        return

    with ui.dialog() as dialog, ui.card():
        ui.label('导入用户信息').classes('text-h5')
        ui.label(
            '请上传CSV文件，包含列: name, password, birth_date, education, gender, training_date')
        ui.upload(on_upload=lambda e: import_users(
            e, dialog)).props('accept=.csv')
        ui.button('取消', on_click=dialog.close)


def import_users(e, dialog):
    try:
        df = pd.read_csv(e.content)
        required_cols = ['name', 'password', 'birth_date',
                         'education', 'gender', 'training_date']
        if not all(col in df.columns for col in required_cols):
            ui.notify('CSV格式不正确，请检查列名', type='negative')
            return

        conn = get_db_connection()
        c = conn.cursor()
        success_count = 0
        for _, row in df.iterrows():
            try:
                hashed_pwd = hash_password(str(row['password']))
                c.execute('''
                    INSERT INTO users (name, password, birth_date, education, gender, training_date, role, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (row['name'], hashed_pwd, row['birth_date'], row['education'],
                      row['gender'], row['training_date'], 'user', datetime.now().isoformat()))
                success_count += 1
            except sqlite3.IntegrityError:
                continue
        conn.commit()
        conn.close()
        ui.notify(f'成功导入 {success_count} 个用户', type='positive')
        dialog.close()
    except Exception as e:
        ui.notify(f'导入失败: {str(e)}', type='negative')


def show_export_users():
    if current_role != 'admin':
        ui.notify('权限不足', type='negative')
        return

    with ui.dialog() as dialog, ui.card():
        ui.label('导出用户信息').classes('text-h5')
        export_type = ui.select('导出格式', ['CSV', 'Excel'])

        def do_export():
            conn = get_db_connection()
            df = pd.read_sql_query(
                'SELECT name, birth_date, education, gender, training_date, role FROM users', conn)
            conn.close()
            filename = f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            if export_type.value == 'CSV':
                df.to_csv(f'{filename}.csv', index=False)
                ui.notify(f'导出为 {filename}.csv', type='positive')
            else:
                df.to_excel(f'{filename}.xlsx', index=False)
                ui.notify(f'导出为 {filename}.xlsx', type='positive')
            dialog.close()

        with ui.row():
            ui.button('导出', on_click=do_export).classes(
                'bg-blue-500 text-white')
            ui.button('取消', on_click=dialog.close)
    dialog.open()


def show_main_content():
    global main_content
    if main_content:
        main_content.clear()

    with main_content:
        ui.label('欢迎使用用户管理系统').classes('text-h4 text-center w-full')
        ui.label('请从左侧菜单选择操作').classes('text-center w-full text-gray-500')

# 主页面


@ui.page('/')
def home_page():
    global current_user, current_role, main_content
    print(f'{current_user=}, {current_role=}, {main_content=}')
    ui.label('Home page')


# 用户页面
@ui.page('/user_page')
def user_page():
    global current_user, current_role, main_content

    with ui.header().classes('items-center justify-between'):
        ui.label('用户管理系统').classes('text-h5')
        if current_user:
            ui.label(f'当前用户: {current_user} ({current_role})')
            ui.button('退出', on_click=logout).classes('bg-red-500 text-white')

    with ui.row().classes('w-full'):
        # 左侧导航
        with ui.column().classes('w-1/6 p-4'):
            ui.button('注册', on_click=show_register,
                      icon='person_add').classes('w-full m-1')
            ui.button('登录', on_click=show_login,
                      icon='login').classes('w-full m-1')
            if current_role == 'admin':
                ui.button('用户管理', on_click=show_user_management,
                          icon='people').classes('w-full m-1')
                ui.button('导入用户', on_click=show_import_users,
                          icon='upload').classes('w-full m-1')
                ui.button('导出用户', on_click=show_export_users,
                          icon='download').classes('w-full m-1')
                ui.button('高级筛选', on_click=show_filter_users,
                          icon='filter_list').classes('w-full m-1')
            elif current_role == 'user':
                ui.button('个人信息', on_click=show_user_profile,
                          icon='person').classes('w-full m-1')
            # 预留新功能入口
            ui.separator()
            ui.button('新功能1', on_click=lambda: ui.notify(
                '新功能1开发中...')).classes('w-full m-1 bg-gray-200')
            ui.button('新功能2', on_click=lambda: ui.notify(
                '新功能2开发中...')).classes('w-full m-1 bg-gray-200')

        # 主要内容区域
        main_content = ui.column().classes('w-5/6 p-4')
        show_main_content()


# 启动应用
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='用户管理系统', port=8080)
