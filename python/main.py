"""
File: main.py
Author: Chuncheng Zhang
Date: 2026-06-18
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Main entrance for the project.

Functions:
    1. Requirements and constants
    2. Function and class
    3. Play ground
    4. Pending
    5. Pending
"""


# %% ---- 2026-06-18 ------------------------
# Requirements and constants
from typing import Optional
from datetime import datetime
import contextlib
from page_components.layout import with_layout
from nicegui import app, ui
from fastapi import Request
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from omegaconf import OmegaConf

from auth.models import RoleEnum
from auth.database import DatabaseManager
from auth.decorators import AuthContext
from auth.user_service import UserService
from auth.auth_manager import PermissionManager

from session.user_session_manager import UserSessionManager

# %%
# Constant

# Add static directory - This must be done BEFORE any UI elements
app.add_static_files('/static', 'static')  # URL path, local folder %%

# The urls without requiring auth
UNRESTRICTED_PAGE_ROUTES = {'/login', '/welcome', '/', '/static/favicon/*'}

PROJECT = OmegaConf.load('conf/project.yml')

# %%
# Auth system

# Auth db
# 1. 初始化数据库
db_manager = DatabaseManager('sqlite:///db/auth.db', echo=False)
db_manager.create_tables()
db_manager.initialize_data()

# 2. 创建服务实例
session = db_manager.get_session()
user_service = UserService(session)
permission_manager = PermissionManager(session)
auth_context = AuthContext(user_service, permission_manager)

try:
    # 创建测试用户
    # 创建管理员
    admin1 = user_service.create_user(
        username='admin',
        password='admin',
        role=RoleEnum.ADMIN.value
    )

    # 创建普通用户
    user1 = user_service.create_user(
        username="testuser",
        password="password123",
        role=RoleEnum.USER.value
    )

    # 创建访客
    guest = user_service.create_user(
        username="guest",
        password="guest123",
        role=RoleEnum.GUEST.value
    )
except:
    pass

# Auth middle ware
session_manager = UserSessionManager()


# %% ---- 2026-06-18 ------------------------
# Function and class
@app.add_middleware
class EnhancedAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.user_sessions = {}  # {user_id: {sessions}}

    async def dispatch(self, request: Request, call_next):
        # 获取会话ID
        session_id = request.cookies.get('session_id')
        user_id = None

        if session_id and session_id in session_manager.active_sessions:
            # 更新活动时间
            session_manager.update_activity(session_id)
            user_data = session_manager.active_sessions[session_id]
            user_id = user_data.get('id')

            # 存储到请求状态
            request.state.user = user_data

        # 检查认证
        # if not user_id and not request.url.path.startswith('/_nicegui') \
        #    and request.url.path not in unrestricted_page_routes:
        #     return RedirectResponse(f'/login?redirect_to={request.url.path}')

        # 检查认证
        if not app.storage.user.get('authenticated', False):
            if not request.url.path.startswith('/_nicegui') and request.url.path not in UNRESTRICTED_PAGE_ROUTES:
                return RedirectResponse(f'/login?redirect_to={request.url.path}')

        response = await call_next(request)

        # 如果设置了新的会话，添加到cookie
        if hasattr(request.state, 'new_session_id'):
            response.set_cookie(
                key='session_id',
                value=request.state.new_session_id,
                httponly=True,
                max_age=3600 * 24  # 24小时
            )

        return response


@contextlib.contextmanager
def make_it_center():
    with ui.column().classes('absolute-center items-center') as col:
        yield col
    return


@ui.page('/welcome')
@with_layout
async def welcome_page():
    with make_it_center():
        ui.label('Welcome to my project.')
        user = app.storage.user
        if not user.get('authenticated', False):
            ui.label('You have not logged in.').classes('text-negative')
            ui.link('Login', '/login')
        else:
            ui.label(f'Dear {user.get("username", "N.A.")}').classes(
                'text-positive')
    return


@ui.page('/')
@with_layout
async def root():

    with make_it_center():
        # ui.link('Welcome page', '/welcome')
        # ui.link('Profile page', '/profile')
        # with ui.card().classes('max-w-3xl w-full shadow-lg'):
        #     ui.markdown(abstract)
        pass

    # 快速导航按钮
    with ui.row().classes('gap-4 mt-8'):
        if app.storage.user.get('authenticated', False):
            ui.button('Profile', icon='dashboard',
                      on_click=lambda: ui.navigate.to('/profile')).props('color=primary')
            ui.button('Experiments', icon='sensors',
                      on_click=lambda: ui.navigate.to('/experiments')).props('color=secondary')
            ui.button('Others', icon='science',
                      on_click=lambda: ui.navigate.to('/others')).props('color=accent')
        else:
            ui.button('立即登录', icon='login',
                      on_click=lambda: ui.navigate.to('/login')).props('color=primary')
            ui.button('了解更多', icon='info',
                      on_click=lambda: ui.navigate.to('/welcome')).props('flat')

    # 使用markdown并添加卡片样式
    abstract = PROJECT['abstract']
    with ui.card().classes('max-w-3xl w-full shadow-lg bg-white/40'):
        with ui.card_section().classes('p-8'):
            ui.markdown(abstract).classes(
                'text-gray-700 leading-relaxed'
            )

    return


@ui.page('/login')
@with_layout
async def login(redirect_to: str = '/') -> Optional[RedirectResponse]:
    def try_login() -> None:  # local function to avoid passing username and password as arguments
        user = user_service.authenticate_user(username.value, password.value)
        if user is not None:
            app.storage.user.update(
                {'username': username.value,
                 'authenticated': True,
                 'id': user.id,
                 'logInTime': datetime.now()
                 })
            session_id = session_manager.add_session(app.storage.user)
            app.storage.user.update(
                {'session_id': session_id}
            )
            # go back to where the user wanted to go
            ui.navigate.to(redirect_to)
        else:
            ui.notify('Wrong username or password', color='negative')

    if app.storage.user.get('authenticated', False):
        # return RedirectResponse('/')
        # ui.navigate.to('/')
        return

    with ui.card().classes('absolute-center'):
        ui.label('Login')
        username = ui.input('Username').on('keydown.enter', try_login)
        password = ui.input('Password', password=True, password_toggle_button=True).on(
            'keydown.enter', try_login)
        ui.button('Log in', on_click=try_login)
        ui.link('Continue without login', '/welcome')
    return

# %% ---- 2026-06-18 ------------------------
# Play ground


# %% ---- 2026-06-18 ------------------------
# Pending


# %% ---- 2026-06-18 ------------------------
# Running
if __name__ in {'__main__', '__mp_main__'}:
    import sys

    kwargs = {
        'reload': True,
    }
    if len(sys.argv) > 1 and sys.argv[1] == '-w':
        kwargs = {
            'reload': False,
            'frameless': True,
            'window_size': (1440, 900),
        }

    ui.run(root,
           title=PROJECT.get('name', 'Project'),
           favicon='./static/favicon/favicon.ico',
           uvicorn_reload_excludes='.*, .py[cod], .sw.*, ~*, *.db, *.log, fds, hysplit',
           storage_secret='abcdefg',
           **kwargs)
