import asyncio
import sys
import subprocess
from nicegui import ui, events
from pathlib import Path
from datetime import datetime

sys.path.append('..')  # noqa
from constants import *
from experiments import Experiments
from auth.user_service import UserService

CONDA_ENV = 'gyhtyzx'

EXP = Experiments()

# class EXP:
#     a = dict(
#         cn='单音节分辨',
#         script='./experiments/script/单音节分辨.py',
#         abstract='abstract')


def run_experiment(dct, output_dir):
    subprocess.run(['conda', 'run', '-n', CONDA_ENV, 'python',
                   dct['script'], '--path', output_dir.as_posix()])
    # import time
    # time.sleep(1)  # Simulate work
    return


async def start_experiment(event: events.ClickEventArguments, dct: dict, uuid: str = 'uuid'):
    btn = event.sender

    try:
        btn.disable()

        output_dir = Path(
            './data', uuid, dct['cn'], datetime.strftime(datetime.now(), FILE_DATE_FMT))

        ui.notify(
            f'Start experiment: {dct=}, {output_dir=}', **NOTIFY_KWARGS.positive)

        # Run blocking code in thread
        await asyncio.to_thread(run_experiment, dct, output_dir)

    finally:
        btn.enable()

    return


def experiments_gallery(id: int, uuid: str, user_service: UserService):

    if not user_service.get_user_by_id(id).has_permission('perform_experiment1'):
        ui.label('Permission deny').classes(STYLES.errorText)

    exps = {}
    # with ui.card().classes(STYLES.fullCard):
    with ui.row().classes('w-full gap-2 justify-center'):
        # ----------------------------------------------------------------------
        for exp in EXP.experiments:
            exps[exp['script']] = exp
            card = ui.card().classes(STYLES.column4Card)
            with card:
                ui.label(exp['cn']).classes(STYLES.cardTitleLabel)
                ui.label(exp['folder'])
                ui.textarea(value=exp['abstract']).classes(
                    'w-full').props('readonly')
                ui.button(
                    'Launch', on_click=lambda e, exp=exp: start_experiment(e, exp, uuid))

    return
