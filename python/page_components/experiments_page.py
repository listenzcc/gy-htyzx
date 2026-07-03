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


def run_experiment(dct, output_dir, input_options):
    kwargs = {e: v.value for e, v in input_options.items()}
    commands = ['conda', 'run', '-n', CONDA_ENV,
                'python', dct['script'],
                '--path', output_dir.as_posix()]
    for e, v in kwargs.items():
        if v:
            commands.extend([f'--{e}', v])
    print(commands)
    return
    subprocess.run(['conda', 'run', '-n', CONDA_ENV, 'python',
                   dct['script'], '--path', output_dir.as_posix()])
    # import time
    # time.sleep(1)  # Simulate work
    return


async def start_experiment(event: events.ClickEventArguments, dct: dict, uuid: str = 'uuid', input_options=None):
    btn = event.sender

    try:
        btn.disable()

        output_dir = Path(
            './data', uuid, dct['cn'], datetime.strftime(datetime.now(), FILE_DATE_FMT))

        ui.notify(
            f'Start experiment: {dct=}, {output_dir=}', **NOTIFY_KWARGS.positive)

        # Run blocking code in thread
        await asyncio.to_thread(run_experiment, dct, output_dir, input_options)

    finally:
        btn.enable()

    return


def experiments_gallery(id: int, uuid: str, user_service: UserService):

    if not user_service.get_user_by_id(id).has_permission('perform_experiment1'):
        ui.label('Permission deny').classes(STYLES.errorText)

    from collections import defaultdict
    exps = {}
    type_field = {}
    input_options = defaultdict(dict)

    # with ui.card().classes(STYLES.fullCard):
    row_styles = 'w-full gap-4 justify-center items-start'
    with ui.row().classes('w-full gap-2 justify-center'):
        for type_name in EXP.type_dct.keys():
            with ui.expansion(type_name).classes('w-full gap-2 justify-center'):
                type_field[type_name] = ui.row().classes(row_styles)

        # ----------------------------------------------------------------------
        for exp in EXP.experiments:
            exps[exp['script']] = exp
            types = exp.get('type')
            options = exp.get('options', [])

            with type_field[types[0]]:
                card = ui.card().classes(STYLES.column4Card)
                with card:
                    ui.label(exp['cn']).classes(STYLES.cardTitleLabel)
                    ui.label(exp['folder'])
                    ui.label('/'.join(types))
                    ui.textarea(value=exp.get('abstract', '--')).classes(
                        'w-full').props('readonly')

                    use_default_value = True
                    if options:
                        with ui.expansion('实验选项').classes('w-full'):
                            for opt in options:
                                if opt.startswith('#'):
                                    use_default_value = False

                                if not opt.startswith('-'):
                                    ui.label(opt)
                                    continue

                                opt = opt.replace(
                                    '-', '').replace(',', ' ').replace(':', ' ').strip()
                                opts = [e.strip()
                                        for e in opt.split() if e.strip()]

                                n = opts[0]
                                t = opts[1]
                                if t == 'int':
                                    values = [int(opts[2]), int(opts[3])]
                                    with ui.row().classes('w-full'):
                                        input_options[exp['script']][n] = ui.number(
                                            label=f'{n}({t})', min=values[0], max=values[1], step=1, value=values[0] if use_default_value else None).classes('w-full')
                                elif t == 'float':
                                    values = [float(opts[2]), float(opts[3])]
                                    step = (values[1] - values[0]) / 100
                                    with ui.row().classes('w-full'):
                                        input_options[exp['script']][n] = ui.number(
                                            label=f'{n}({t})', min=values[0], max=values[1], step=step, value=values[0] if use_default_value else None).classes('w-full')
                                elif t == 'option':
                                    values = opts[2:]
                                    input_options[exp['script']][n] = ui.select(
                                        options=values, label=f'{n}({t})', value=values[0] if use_default_value else None).classes('w-full')
                                else:
                                    ui.label(opt).classes(STYLES.errorText)

                    ui.button(
                        'Launch', on_click=lambda e, exp=exp: start_experiment(e, exp, uuid, input_options[exp['script']]))

    return
