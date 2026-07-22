# ------------------------------------------------------------------------------
from omegaconf import OmegaConf
from collections import defaultdict
import os
import sys
import shutil
import asyncio
import subprocess
from loguru import logger
from pathlib import Path
from nicegui import ui, events
from datetime import datetime

# ------------------------------------------------------------------------------
sys.path.append('..')  # noqa
from constants import *
from experiments import Experiments
from stimulation_plans import SimulationParameters
from auth.user_service import UserService

# ------------------------------------------------------------------------------
logger.add("log/experiment_{time:YYYY-MM-DD}.log",
           encoding=ENCODING, rotation='1 day')

# ------------------------------------------------------------------------------
EXP = Experiments()


# ------------------------------------------------------------------------------
def run_experiment(dct, output_dir: Path, input_options: dict):
    def _safe_int(value):
        if isinstance(value, float) and value % 1 == 0:
            return int(value)
        return value

    kwargs = {e: _safe_int(v.value) for e, v in input_options.items()}
    src = Path(dct['script']).absolute()
    dst = output_dir.absolute()
    commands = [
        # 'conda', 'run', '-n', CONDA_ENV,
        'python', src.as_posix(),
        '--path', dst.as_posix()]

    for e, v in kwargs.items():
        if v:
            commands.extend([f'--{e}', str(v)])

    if output_dir.is_dir():
        logger.warning(f'Dir exists: {output_dir}')
    else:
        output_dir.mkdir(exist_ok=True, parents=True)

    # Record commands
    print(commands, file=open(output_dir /
          'experiment.commands', 'w', encoding=ENCODING))
    logger.debug(f'Using {commands=}')

    # Actually running the experiment
    _stdout = open(output_dir / 'experiment.stdout', 'w', encoding=ENCODING)
    _stderr = open(output_dir / 'experiment.stderr', 'w', encoding=ENCODING)
    try:
        completed = subprocess.run(
            commands, cwd=src.parent, stdout=_stdout, stderr=_stderr,
            encoding=ENCODING,
            env={**os.environ, 'PYTHONIOENCODING': ENCODING}  # 设置 Python 环境变量
        )
        assert completed.returncode == 0, '执行完毕但 returncode 不为 0。'
        print(completed, file=open(output_dir /
              'experiment.finish', 'w', encoding=ENCODING))
        logger.info(f'Experiment finished: {commands=}')

        # ! Simulation for data acquirement
        if dct.get('requireEEG'):
            example_fname = Path(
                f'./workshop/eeg/data/{src.name.split("_")[0]}-raw.cnt')
            assert example_fname.is_file(), f'File error: {example_fname}'
            shutil.copy(example_fname, dst / 'experiment-raw.cnt')

    except Exception as err:
        logger.error(f'Experiment failed: {err=}')
        with open(output_dir / 'experiment.error', 'w', encoding=ENCODING) as file:
            file.write(f'{err=}\r\n')
            import traceback
            file.write(traceback.format_exc())

    return


async def start_experiment(event: events.ClickEventArguments, dct: dict, uuid: str = 'uuid', input_options=None):
    btn = event.sender

    try:
        btn.disable()

        output_dir = Path(
            './data', uuid, Path(dct['script']).stem, datetime.strftime(datetime.now(), FILE_DATE_FMT))

        ui.notify(
            f'Start experiment: {dct=}, {output_dir=}', **NOTIFY_KWARGS.positive)

        # Run blocking code in thread
        await asyncio.to_thread(run_experiment, dct, output_dir, input_options)

    finally:
        btn.enable()
        btn._text = '（执行完毕）'
        btn.update()

    return


def stimulation_plan_gallery(id: int, uuid: str, user_service: UserService):

    if not user_service.get_user_by_id(id).has_permission('perform_experiment1'):
        ui.label('Permission deny').classes(STYLES.errorText)
        return

    ui.label('刺激方案').classes(STYLES.cardTitleLabel)
    try:
        file_ = './workshop/plans/stimulation-plans.yml'
        plans = OmegaConf.load(file_)
    except Exception as err:
        ui.label(f'读取方案失败 {err}，请检查 {file_}').classes(STYLES.errorText)
        return

    params = SimulationParameters()

    # 设置参数 (匹配示例)
    params.mode = '方案A'
    params.channel = '通道1'
    params.light_wavelength = 810
    params.light_frequency = 50
    params.light_power = 30
    params.current_intensity = 1.5
    params.elec_frequency = 20
    params.stimulation_duration = 40

    options = {v: v['name'] for k, v in plans.items()}
    plan_select = ui.select(options, label='选择刺激方案').classes('w-full')
    with ui.card().classes('w-full'):
        plan_row = ui.row().classes('w-full justify-evenly')
    with plan_row:
        ui.label('选择刺激方案后，参数会显示在这里')

    plan_select.on_value_change(lambda: _select_plan())

    def _select_plan():
        plan = plan_select.value
        for k, v in plan.items():
            params.__setattr__(k, v)
        plan_row.clear()
        plan_card_inputs = {}
        with plan_row:
            with ui.card().classes(STYLES.column4Card):
                ui.label(plan['name']).classes(STYLES.cardSubTitleLabel)
                plan_card_inputs['mode'] = ui.select(
                    label='mode', value=params.mode, options=['模式A', '模式B', '模式C']).classes('w-full')
                plan_card_inputs['channel'] = ui.select(
                    label='channel', value=params.channel, options=['通道1', '通道2', '双通道']).classes('w-full')
                plan_card_inputs['light_wavelength'] = ui.number(
                    'light_wavelength', value=params.light_wavelength)
                plan_card_inputs['light_frequency'] = ui.number(
                    'light_frequency', value=params.light_frequency)
                plan_card_inputs['light_power'] = ui.number(
                    'light_power', value=params.light_power)
                plan_card_inputs['current_intensity'] = ui.number(
                    'current_intensity', value=params.current_intensity)
                plan_card_inputs['elec_frequency'] = ui.number(
                    'elec_frequency', value=params.elec_frequency)
                plan_card_inputs['stimulation_duration'] = ui.number('stimulation_duration',
                                                                     value=params.stimulation_duration)
            with ui.card().classes(STYLES.column3_2Card + ' items-center'):
                plan_command_label = ui.label('')
                ui.image(source=Path('./workshop/plans/eeg-1020-layout.png'))
                btn = ui.button(
                    '开始刺激', on_click=lambda: _on_click_plan_start_btn())
                # spinner 默认隐藏
                spinner = ui.spinner(size='lg').classes('mt-2')
                spinner.visible = False
                spinner_label = ui.label()
                spinner_label.visible = False

            async def _countdown(seconds):
                spinner.visible = True
                spinner_label.visible = True

                for remain in range(seconds, 0, -1):
                    spinner_label.text = f'剩余 {remain} 秒'
                    spinner_label.update()
                    await asyncio.sleep(1)

                spinner.visible = False
                spinner_label.visible = False
                spinner.update()
                spinner_label.update()
                return

            async def _on_click_plan_start_btn():
                plan_dct = {k: v.value for k, v in plan_card_inputs.items()}
                ui.notify(f'开始光电刺激：{plan_dct}', **NOTIFY_KWARGS.positive)
                duration = int(plan_dct['stimulation_duration'])
                await _countdown(duration)

        def _plan_card_inputs_on_change():
            for k, inp in plan_card_inputs.items():
                params.__setattr__(k, inp.value)
            frame = params.translate_into_bytes()
            generated_hex = frame.hex().upper()
            plan_command_label.text = f'控制指令：{generated_hex}'

        for k, inp in plan_card_inputs.items():
            inp.on_value_change(_plan_card_inputs_on_change)
        _plan_card_inputs_on_change()

    return


def experiments_plan_gallery(id: int, uuid: str, user_service: UserService):

    if not user_service.get_user_by_id(id).has_permission('perform_experiment1'):
        ui.label('Permission deny').classes(STYLES.errorText)
        return

    ui.label('任务方案').classes(STYLES.cardTitleLabel)

    try:
        file_ = './workshop/plans/training-plans.yml'
        plans = OmegaConf.load(file_)
    except Exception as err:
        ui.label(f'读取方案失败 {err}，请检查 {file_}').classes(STYLES.errorText)
        return

    options = {v: v['name'] for k, v in plans.items()}
    options.update({'': '开始新的方案'})
    plan_select = ui.select(options, label='选择实验方案').classes('w-full')
    plan_edit = ui.textarea(label='实验方案编辑器').classes('w-full')
    plan_edit.set_visibility(False)

    with ui.card().classes('w-full'):
        plan_pipeline_row = ui.row().classes('w-full justify-center')

    with plan_pipeline_row:
        ui.label('选择实验方案后，实验序列会显示在这里')

    plan_select.on_value_change(lambda: _select_plan())
    plan_edit.on_value_change(lambda: _edit_plan())

    input_options = defaultdict(dict)

    def _prepare_tasks(tasks):
        exps = {}
        for cn in tasks:
            exp = [e for e in EXP.experiments if e['cn'] == cn]
            exps[cn] = exp[0] if len(exp) > 0 else None

        with plan_pipeline_row:
            for k, exp in exps.items():
                card = ui.card().classes(STYLES.column4Card)
                with card:
                    ui.label(k).classes(STYLES.cardTitleLabel)
                    if not exp:
                        ui.label(
                            '该任务没有找到，请检查 ./workshop/task/script 目录').classes(STYLES.errorText)
                        continue
                    _put_exp_here(exp, uuid, input_options)

        return

    def _edit_plan():
        input_options.clear()
        plan_pipeline_row.clear()

        tasks = [e.strip() for e in plan_edit.value.split('\n') if e.strip()]

        _prepare_tasks(tasks)

        pass

    def _select_plan():
        input_options.clear()
        plan_pipeline_row.clear()
        plan_edit.set_visibility(False)

        plan = plan_select.value
        if plan is '':
            plan_edit.set_value(
                '\n'.join([e['cn'] for e in EXP.experiments]))
            plan_edit.set_visibility(True)
        else:
            plan_edit.set_value('\n'.join(plan['pipeline']))

        # tasks = [e.strip() for e in plan_edit.value.split('\n') if e.strip()]

        # _prepare_tasks(tasks)

        return


def _put_exp_here(exp, uuid, input_options):
    types = exp.get('type')
    options = exp.get('options', [])

    ui.label(exp['script']).classes('text-sm')
    ui.label('>'.join(types))
    ui.textarea(value=exp.get('abstract', '--')).classes(
        'w-full').props('readonly')

    options = exp['formatted_options']
    with ui.expansion('实验选项').classes('w-full'):
        for opt in options:
            if opt['type'] == 'mention':
                ui.label(opt['content']).classes(
                    STYLES.errorText)
            elif opt['type'] == 'int':
                input_options[exp['script']][opt['name']] = ui.number(
                    label=opt['name'], min=opt['min'], max=opt['max'], step=opt['step'], value=opt['value']).classes('w-full')
            elif opt['type'] == 'float':
                input_options[exp['script']][opt['name']] = ui.number(
                    label=opt['name'], min=opt['min'], max=opt['max'], step=opt['step'], value=opt['value']).classes('w-full')
            elif opt['type'] == 'option':
                input_options[exp['script']][opt['name']] = ui.select(
                    label=opt['name'], options=opt['options'], value=opt['value']).classes('w-full')

    btn = ui.button(
        '开始任务', on_click=lambda e, exp=exp: start_experiment(e, exp, uuid, input_options[exp['script']]))

    return


def experiments_gallery(id: int, uuid: str, user_service: UserService):

    if not user_service.get_user_by_id(id).has_permission('perform_experiment1'):
        ui.label('Permission deny').classes(STYLES.errorText)
        return

    exps = {}
    type_field = {}
    input_options = defaultdict(dict)

    ui.label('单次任务').classes(STYLES.cardTitleLabel)

    # with ui.card().classes(STYLES.fullCard):
    row_styles = 'w-full gap-4 justify-center items-start'
    with ui.row().classes('w-full gap-2 justify-center'):
        for type_name, sub_type_names in EXP.type_dct.items():
            if sub_type_names:
                text = f'{type_name} > {" | ".join(sorted(sub_type_names))}'
            else:
                text = f'{type_name}'
            with ui.expansion(text).classes('w-full gap-2 justify-center') as _expansion:
                type_field[type_name] = ui.row().classes(row_styles)

        # Open the latest expansion
        # _expansion.set_value(True)

        # ----------------------------------------------------------------------
        for exp in EXP.experiments:
            exps[exp['script']] = exp
            types = exp.get('type')
            options = exp.get('options', [])

            with type_field[types[0]]:
                card = ui.card().classes(STYLES.column4Card)
                with card:
                    ui.label(exp['cn']).classes(STYLES.cardTitleLabel)
                    _put_exp_here(exp, uuid, input_options)

    return
