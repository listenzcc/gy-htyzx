import sys
import subprocess
from nicegui import ui
from pathlib import Path
from datetime import datetime

sys.path.append('..')  # noqa
from constants import *
from auth.user_service import UserService

CONDA_ENV = 'gyhtyzx'


class EXP:
    a = dict(
        cn='单音节分辨',
        script='./experiments/script/单音节分辨.py',
        abstract='abstract')


def start_experiment(dct: dict, uuid: str = 'uuid'):
    ui.notify(f'Start experiment: {dct=}', **NOTIFY_KWARGS.positive)
    output_dir = f'./data/{uuid}/{dct["cn"]}'
    subprocess.run(['conda', 'run', '-n', CONDA_ENV, 'python',
                   dct['script'], '--path', output_dir])


def experiments_gallery(id: int, uuid: str, user_service: UserService):

    if not user_service.get_user_by_id(id).has_permission('perform_experiment1'):
        ui.label('Permission deny').classes(STYLES.errorText)

    with ui.card().classes(STYLES.fullCard):
        # ----------------------------------------------------------------------
        card = ui.card().classes(STYLES.columnCard)
        exp = EXP.a
        with card:
            ui.label(exp['cn']).classes(STYLES.cardTitleLabel)
            ui.label(exp['script'])
            ui.textarea(value=exp['abstract'])
            ui.textarea(value=open(exp['script'], encoding='utf-8').read())
            ui.button('Launch', on_click=lambda _: start_experiment(exp, uuid))
        card_a = card

    return
