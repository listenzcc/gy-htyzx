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
from constants import *
from page_components.experiments_page import experiments_gallery
from page_components.headers import reuseable_header
from page_components.login_page import login_login_card, login_signup_card
from page_components.user_management_page import user_management_users
from page_components.debug_block import debug_block
from page_components.profile_page import profile_content_readonly

import contextlib
from typing import Optional
from datetime import datetime
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

from loguru import logger

# %%
logger.add('log/main.log', rotation='5MB')


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


# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
@ui.page('/profile')
@with_layout
async def profile_page():
    id = app.storage.user.get('id')
    user = user_service.get_user_by_id(id)

    # Not login
    if user is None or not user.has_permission('just_walk_by'):
        with make_it_center():
            ui.label('用户未登陆，这通常不会发生。').classes('text-red-500')
        logger.error('Requiring /profile page but not authenticated.')
        return

    reuseable_header('Profile', user.username)

    # Already login
    dct = user.to_dict()
    dct.update({
        'last_login': app.storage.user['last_login'],
        'session_id': app.storage.user['session_id']
    })

    profile_content_readonly(dct)

    debug_block(f'{app.storage.user=}')

    return


# ------------------------------------------------------------------------------
@ui.page('/user_management')
@with_layout
async def user_management_page():
    id = app.storage.user.get('id')
    user = user_service.get_user_by_id(id)

    # Not login
    if user is None or not user.has_permission('just_walk_by'):
        with make_it_center():
            ui.label('用户权限不足。').classes('text-red-500')
        logger.error('Requiring /user_management page but not authenticated.')
        return

    # Check permission
    if not user.has_permission('view_users'):
        with make_it_center():
            ui.label('您没有查看用户的权限。').classes('text-red-500')
        logger.error('Requiring /user_management page but has no premission.')
        return

    reuseable_header('User Management')

    def _on_edit_apply(updated: dict):
        user_service.edit_user_comprehensive(updated)

    user_management_users(id, user_service, on_edit_apply=_on_edit_apply)

    debug_block(f'{app.storage.user=}')
    return

# ------------------------------------------------------------------------------


@ui.page('/experiments')
@with_layout
async def experiments_page():
    id = app.storage.user.get('id')
    user = user_service.get_user_by_id(id)

    # Not login
    if user is None or not user.has_permission('just_walk_by'):
        with make_it_center():
            ui.label('用户未登陆，这通常不会发生。').classes('text-red-500')
        logger.error('Requiring /experiments page but not authenticated.')
        return

    reuseable_header('Experiments', user.username)

    experiments_gallery(user.id, user.uuid, user_service)
    return

# ------------------------------------------------------------------------------


@ui.page('/intro')
@with_layout
async def intro_page():
    id = app.storage.user.get('id')
    user = user_service.get_user_by_id(id)

    # Not login
    if user is None or not user.has_permission('just_walk_by'):
        with make_it_center():
            ui.label('用户未登陆，这通常不会发生。').classes('text-red-500')
        logger.error('Requiring /intro page but not authenticated.')
        return

    reuseable_header('Intro', user.username)
    return


# ------------------------------------------------------------------------------
@ui.page('/login')
@with_layout
async def login_page(redirect_to: str = '/') -> Optional[RedirectResponse]:

    # Navigate to /profile if user is already login.
    if app.storage.user.get('authenticated', False):
        ui.navigate.to('/profile')
        return

    records = []

    def on_success_new_user(value=None):
        if value is not None:
            records.append(value)

        n = len(records)

        if n == 0:
            contents = ['[No new user]']
        else:
            contents = [f'[{n-i}]: {e}' for i, e in enumerate(records[::-1])]

        new_users_ta.set_value('\n'.join(contents))
        return

    reuseable_header('Login & Signup')
    with ui.row().classes('w-full justify-evenly'):
        login_login_card(user_service, session_manager, app, redirect_to)
        login_signup_card(user_service, on_success_new_user)

    ui.separator()

    # with ui.row().classes('w-full justify-evenly'):
    ui.label('New users').classes(STYLES.cardTitleLabel)
    new_users_ta = ui.textarea().classes('w-full')

    on_success_new_user()

    return

# ------------------------------------------------------------------------------


@ui.page('/')
@with_layout
async def root():
    # 快速导航按钮
    with ui.row().classes('gap-4 mt-8 w-full'):
        # Check if use is authenticated
        if app.storage.user.get('authenticated', False):
            ui.button('Profile', icon='dashboard',
                      on_click=lambda: ui.navigate.to('/profile')).props('color=primary')
            ui.button('Experiments', icon='science',
                      on_click=lambda: ui.navigate.to('/experiments')).props('color=accent')
            ui.button('User Management', icon='book',
                      on_click=lambda: ui.navigate.to('/user_management')).props('color=green')
            ui.button('Others', icon='sensors',
                      on_click=lambda: ui.navigate.to('/others')).props('color=secondary')
        else:
            ui.button('立即登录', icon='login',
                      on_click=lambda: ui.navigate.to('/login')).props('color=primary')
            ui.button('了解更多', icon='info',
                      on_click=lambda: ui.navigate.to('/welcome')).props('flat')

    # 使用markdown并添加卡片样式
    abstract = PROJECT['abstract']
    with ui.card().classes('w-full shadow-lg bg-white/40'):
        with ui.card_section().classes('p-8'):
            ui.markdown(abstract,
                        extras=['latex', 'mermaid', 'task_lists', 'code']).classes(
                'text-gray-700 leading-relaxed'
            )

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
           # ! Only reload with these folders are changed.
           uvicorn_reload_dirs='./python',
           storage_secret='abcdefg',
           **kwargs)
