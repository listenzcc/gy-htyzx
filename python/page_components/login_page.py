import sys
from nicegui import ui, App
from datetime import datetime
from .inputs import date_input
from .constants import *

sys.path.append('..')  # noqa
from auth.user_service import UserService
from session.user_session_manager import UserSessionManager


def login_login_card(
        user_service: UserService,
        session_manager: UserSessionManager,
        app: App,
        redirect_to: str,
):

    def try_login():
        user = user_service.authenticate_user(username.value, password.value)
        if user is not None:
            session_id = session_manager.add_session(app.storage.user)
            app.storage.user.update(user.to_dict())
            app.storage.user.update({
                'authenticated': True,
                'last_login': datetime.now().isoformat(),
                'session_id': session_id,
            })
            # go back to where the user wanted to go
            ui.navigate.to(redirect_to)
            return True

        ui.notify('Wrong username or password', color='negative')
        return False

    with ui.card().classes('w-1/3 shadow-lg border'):  # .classes('absolute-center'):
        ui.label('Login').classes('text-2xl font-bold tracking-tight')
        username = ui.input('Username').classes(
            'w-full').on('keydown.enter', try_login)
        password = ui.input('Password', password=True, password_toggle_button=True).classes('w-full').on(
            'keydown.enter', try_login)
        ui.button('Log in', on_click=try_login)
        ui.link('Continue without login', '/welcome')
    return


def login_signup_card(on_edit_apply=None):

    with ui.card().classes('w-1/3 shadow-lg border') as detail_card:
        ui.label('Signup').classes('text-2xl font-bold tracking-tight')

        inputs = {}

        def render_detail():

            detail_card.clear()

            with detail_card:
                ui.label('User Detail').classes('text-lg font-semibold')

                # u is the empty dict
                u = {}

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
                birth = u.get('birth_date') | datetime.now()
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
                    updated['gender'] = inputs['gender'].value
                    updated['is_active'] = inputs['is_active'].value
                    updated['birth_date'] = inputs['birth_date'].value or None
                    updated['training_date'] = inputs['training_date'].value or None

                    if on_edit_apply:
                        on_edit_apply(updated)
                    else:
                        print(f'APPLY, {updated=}')

                    ui.notify('Changes are applied')

                ui.button('Apply', on_click=apply).props('color=primary')
        render_detail()
    return
