import sys
from nicegui import ui, App
from datetime import datetime
from .inputs import date_input

sys.path.append('..')  # noqa
from constants import *
from auth.user_service import UserService
from session.user_session_manager import UserSessionManager

username_validation = {
    '用户名过短': lambda value: len(value) > 3,
    '用户名包含不支持的字符': lambda value: all([e in ALLOWED_USERNAME for e in value])
}

password_validation = {
    '密码过短': lambda value: len(value) > 5,
    '密码包含不支持的字符': lambda value: all([e in ALLOWED_PASSWORD for e in value])
}


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

    with ui.card().classes(STYLES.columnCard):  # .classes('absolute-center'):
        ui.label('Login').classes(STYLES.cardTitleLabel)
        username = ui.input('Username', validation=username_validation).classes(
            'w-full').on('keydown.enter', try_login)
        password = ui.input('Password', password=True, password_toggle_button=True).classes('w-full').on(
            'keydown.enter', try_login)
        ui.button('Log in', on_click=try_login)
        ui.link('Continue without login', '/welcome')
    return


def login_signup_card(user_server: UserService, on_success: None):

    with ui.card().classes(STYLES.columnCard) as detail_card:
        ui.label('Signup').classes(STYLES.cardTitleLabel)

        inputs = {}

        def render_detail():

            detail_card.clear()

            with detail_card:
                ui.label('Signup').classes(STYLES.cardTitleLabel)

                # Init the u as the NEW_USER_DCT
                u = {k: v for k, v in NEW_USER_DCT.items()}

                # Username
                inputs['username'] = ui.input(
                    'Username', value=u.get('username', ''),
                    validation=username_validation
                ).classes('w-full')

                # Password
                def _v():
                    return inputs['password'].value == inputs['confirmPassword'].value
                confirm_password_validation = {
                    k: v for k, v in password_validation.items()}
                confirm_password_validation.update({
                    '密码不一致': lambda _: _v()
                })

                inputs['password'] = ui.input(
                    'Password', password=True, password_toggle_button=True, validation=password_validation).classes('w-full')
                inputs['confirmPassword'] = ui.input(
                    'Confirm Password', password=True, password_toggle_button=True, validation=confirm_password_validation).classes('w-full')

                ui.separator().classes('border-t-2 border-gray-200')

                # Role & active
                with ui.row().classes('w-full row'):
                    inputs['role'] = ui.select(
                        options=list(ROLES),
                        label='Role',
                        value=u.get('role')
                    ).classes('col-5')

                    inputs['is_active'] = ui.switch(
                        'Active', value=u.get('is_active', True))

                # Gender & education
                with ui.row().classes('w-full row'):
                    # Gender
                    inputs['gender'] = ui.select(
                        options=list(GENDERS),
                        label='Gender',
                        value=u.get('gender')
                    ).classes('col-5')

                    # Education
                    education = u.get('education')
                    options = list(EDUCATIONS)
                    if not education in options:
                        options.append(education)
                    inputs['education'] = ui.select(
                        options=options,
                        value=education,
                        label='Education',
                        new_value_mode='add'
                    ).classes('col-5')

                # Birth date & training date
                with ui.row().classes('w-full row'):
                    # Birth
                    birth = u.get('birth_date', datetime.now())
                    inputs['birth_date'] = date_input(
                        'Birth Date', birth.strftime(DATE_FMT)).classes('col-5')

                    # Training
                    training = u.get('training_date', datetime.now())
                    inputs['training_date'] = date_input(
                        'Training Date', training.strftime(DATE_FMT)).classes('col-5')

                # Apply
                def apply():
                    updated = dict(u)

                    updated['role'] = inputs['role'].value.strip()
                    updated['gender'] = inputs['gender'].value
                    updated['username'] = inputs['username'].value.strip()
                    updated['password'] = inputs['password'].value.strip()
                    updated['confirmPassword'] = inputs['confirmPassword'].value.strip()
                    updated['education'] = inputs['education'].value
                    updated['is_active'] = inputs['is_active'].value
                    updated['birth_date'] = datetime.strptime(
                        inputs['birth_date'].value, DATE_FMT)
                    updated['training_date'] = datetime.strptime(
                        inputs['training_date'].value, DATE_FMT)

                    # Check if updated is validated
                    def _check_inputs():
                        for k, foo in username_validation.items():
                            if not foo(updated['username']):
                                ui.notify(k, **NOTIFY_KWARGS.negative)
                                return False
                        if not updated['confirmPassword'] == updated['password']:
                            ui.notify('两次密码不一致', **NOTIFY_KWARGS.negative)
                            return False

                        return True

                    # Do nothing if not checked
                    if not _check_inputs():
                        return

                    # New user does not require confirmPassword.
                    updated.pop('confirmPassword')

                    print(f'APPLY, {updated=}')
                    user = user_server.create_user(**updated)
                    if user is not None:
                        ui.notify('New user is applied',
                                  **NOTIFY_KWARGS.positive)
                        if on_success is not None:
                            record = f'time={user.created_at}; username={user.username}'
                            on_success(record)
                    else:
                        ui.notify('Failed create new user',
                                  **NOTIFY_KWARGS.negative)

                ui.button('Apply', on_click=apply).props('color=primary')
        render_detail()
    return
