
# ------------------------------------------------------------------------------
import pandas as pd
import os
import sys
import shutil
import asyncio
import subprocess
from loguru import logger
from pathlib import Path
from nicegui import ui, events
from datetime import datetime

from .inputs import image_table_txt_select

# ------------------------------------------------------------------------------
sys.path.append('..')  # noqa
from constants import *
from experiments import Experiments, TASK_NAME_EN2CN
from auth.user_service import UserService

# ------------------------------------------------------------------------------
logger.add("log/analysis_{time:YYYY-MM-DD}.log",
           encoding=ENCODING, rotation='1 day')

# ------------------------------------------------------------------------------
EXP = Experiments()

# ------------------------------------------------------------------------------
DATA_FOLDER = Path('./data')


# ------------------------------------------------------------------------------
def render_analysis_page(id: int, uuid: str, user_service: UserService, user_ids: list = []):

    is_admin = user_service.get_user_by_id(id).role == '管理员'

    def has_permission():
        return user_service.get_user_by_id(id).has_permission('analysis_experiment1')

    def fetch_users():
        all_users = sorted(user_service.list_users(), key=lambda e: e.id)

        if not is_admin:
            all_users = [e for e in all_users if e.id == id]

        selected_users = [
            e for e in all_users if not user_ids or e.id in user_ids]
        good_users = [e for e in selected_users if (
            DATA_FOLDER / e.uuid).is_dir()]
        return good_users

    if not has_permission():
        ui.label('Permission deny').classes(STYLES.errorText)
        return

    with ui.card().classes(STYLES.fullCard):
        ui.label('选择要分析的用户').classes(STYLES.cardTitleLabel)
        users = fetch_users()
        if not users:
            ui.label('无可用的待分析数据').classes(STYLES.errorText)
            return

        user_select = ui.select(
            [e.username for e in users], value=users[0].username).classes('w-full')
        user_info = ui.textarea('').classes('w-full')

        ui.separator()

        # Make table
        columns = [
            dict(name='id', label='序号'),
            dict(name='experimentType', label='任务类别'),
            dict(name='experimentCN', label='任务名'),
            dict(name='datetime', label='实验日期'),
        ]

        [e.update({'field': e['name'], 'sortable': True})
            for e in columns]
        date_table = ui.table(rows=[], columns=columns, row_key='id', pagination={
                              'rowsPerPage': 10}).classes('w-full').props('dense bordered flat')

        data_card = ui.card().classes(STYLES.fullCard)
        with data_card:
            ui.label('未选择数据，请选择一个任务开始数据分析').classes(STYLES.cardSubTitleLabel)

        # Look inside the folder

    class Analysis:
        def __init__(self):
            user_select.on_value_change(self._user_select_on_change)
            self._user_select_on_change()
            pass

        def _date_table_on_row_click(self, evt):
            row = evt.args[1]
            username = user_select.value
            user = user_service.get_user_by_username(username)
            folder = DATA_FOLDER / user.uuid / \
                row['experiment'] / row['datetime']
            files = {e: e.relative_to(folder).as_posix()
                     for e in folder.rglob('*') if e.is_file()}
            # Fill data card
            data_card.clear()
            with data_card:
                ui.label(f'“{row["experimentCN"]}”任务').classes(
                    STYLES.cardSubTitleLabel)

                image_table_txt_select(
                    files, '/'.join([row['experiment'], row['datetime']]))

                ui.separator()

                # Search the experiments for scripts
                exp = [e for e in EXP.experiments
                       if e['cn'] == row['experimentCN']]

                # ! Incorrect if not find any
                if not exp:
                    ui.label('没有找到与该任务配套的处理脚本，请检查 workshop 目录').classes(
                        STYLES.errorText)
                    return

                # OK, find one.
                exp = exp[0]

                # Not requireEEG, no further steps are needed
                if not exp.get('requireEEG'):
                    ui.label('该任务不配套脑电数据，因此无须进一步分析').classes(
                        STYLES.cardSubTitleLabel)
                    return

                # Scripts
                # --------------------------------------------------------------
                # Preprocessing script
                ui.label('与该实验有关的预处理脚本').classes(STYLES.cardSubTitleLabel)
                preprocessing_scripts = [
                    e for e in exp['scripts'] if e.name.endswith('_preprocessing.py')]
                if not preprocessing_scripts:
                    ui.label('没有找到与该任务配套的预处理脚本，请检查 workshop 目录').classes(
                        STYLES.errorText)
                    return
                preprocessing_script = preprocessing_scripts[0]
                preprocessing_args = ['--cnt', 'experiment-raw.cnt',
                                      '--out', 'preprocessing']
                preprocessing_args_2 = []
                ui.label(preprocessing_script.as_posix())

                ui.label('可选参数表')
                preprocessing_toggles = {
                    'c 滤波': True,
                    'd 波形图呈现': True,
                    'e 脑地形图呈现': True,
                    'f 坏道检测与插值': True,
                    'g ICA去噪': True,
                    'h 分段提取和噪音试次检测剔除': True}
                with ui.row().classes('w-full'):
                    preprocessing_checkboxes = {}
                    for k, v in preprocessing_toggles.items():
                        cb = ui.checkbox(k, value=v)
                        preprocessing_checkboxes[k] = cb

                        # 监听变化，更新选中列表
                        def update_selection():
                            preprocessing_args_2.clear()
                            for k, cb in preprocessing_checkboxes.items():
                                if not cb.value:
                                    preprocessing_args_2.append(f'--no-{k[0]}')
                            print(preprocessing_args_2)

                        cb.on_value_change(update_selection)
                    pass

                experiment_raw_eeg_file = folder / 'experiment-raw.cnt'
                ui.label('预处理所需的原始数据').classes(STYLES.cardSubTitleLabel)
                ui.label(experiment_raw_eeg_file.as_posix() +
                         ' (或 experiment-raw.fif)')

                preprocessing_results_row = ui.row().classes('w-full')

                def _on_preprocessing_start():
                    preprocessing_spinner.set_visibility(True)

                def _on_preprocessing_finish():
                    print('Preprocessing finish')
                    preprocessing_results_row.clear()
                    with preprocessing_results_row:
                        ui.label('预处理结果').classes(STYLES.cardSubTitleLabel)
                        files = {e: e.relative_to(folder).as_posix()
                                 for e in folder.rglob('*') if e.is_file() and e.relative_to(folder).as_posix().startswith('preprocessing')}
                        image_table_txt_select(
                            files, '/'.join([row['experiment'], row['datetime']]) + '> preprocessing')
                    preprocessing_spinner.set_visibility(False)

                with ui.row():
                    ui.button('开始预处理', on_click=lambda evt,
                              script=preprocessing_script,
                              cwd=folder,
                              args1=preprocessing_args,
                              args2=preprocessing_args_2:
                              start_preprocessing(evt, script, cwd, args1, args2, on_start=_on_preprocessing_start, on_finish=_on_preprocessing_finish))
                    preprocessing_spinner = ui.spinner()

                _on_preprocessing_finish()

                ui.separator()

                # --------------------------------------------------------------
                # Analysis scripts
                ui.label('与该实验有关的特征计算脚本').classes(STYLES.cardSubTitleLabel)
                compute_scripts = sorted([e for e in exp['scripts']
                                          if not e.name.endswith('_preprocessing.py')])
                if not compute_scripts:
                    ui.label('没有找到与该实验有关的特征计算脚本').classes(STYLES.errorText)
                    return

                compute_script_select = ui.select(
                    [e.as_posix() for e in compute_scripts],
                    value=compute_scripts[0].as_posix()).classes('w-full')

                computing_results_row = ui.row().classes('w-full')

                class Compute:
                    script = Path(compute_script_select.value).absolute()
                    _clean_epo = folder / 'preprocessing' / 'clean_epo.fif'
                    args = [
                        '--epo', _clean_epo.absolute().as_posix(),
                        '--out', '.'
                    ]
                    cwd: Path
                    mname: str

                    def __init__(self):
                        compute_script_select.on_value_change(
                            self._script_on_select)
                        self._script_on_select()

                    def _script_on_select(self):
                        self.script = Path(
                            compute_script_select.value).absolute()
                        self.mname = self.script.stem.split('_')[-1]
                        self.cwd = folder / self.mname
                        try:
                            _on_computing_finish()
                        except:
                            pass

                compute = Compute()

                def _on_computing_start():
                    computing_spinner.set_visibility(True)
                    return

                def _on_computing_finish():
                    computing_spinner.set_visibility(False)
                    computing_results_row.clear()
                    with computing_results_row:
                        folder = compute.cwd
                        print(folder)
                        if not folder.is_dir():
                            return
                        ui.label('特征计算结果').classes(STYLES.cardSubTitleLabel)
                        files = {e: e.relative_to(folder).as_posix()
                                 for e in folder.rglob('*') if e.is_file() and e.relative_to(folder).as_posix().startswith(compute.mname)}
                        image_table_txt_select(
                            files, '/'.join([row['experiment'], row['datetime']]) + f'> {compute.mname}')
                    return

                with ui.row():
                    ui.button('开始特征计算', on_click=lambda evt,
                              compute=compute:
                              start_computing(evt, compute, on_start=_on_computing_start, on_finish=_on_computing_finish))
                    computing_spinner = ui.spinner()

                _on_computing_finish()

                return

        def _user_select_on_change(self):
            # Change user info
            username = user_select.value
            user = user_service.get_user_by_username(username)
            user_info.set_value(f'{user.to_dict()}')

            user_folder = DATA_FOLDER / user.uuid

            # Find the {uuid}/{datetime} sub folders in the user_folder
            task_folders = sorted(
                [e for e in user_folder.iterdir() if e.is_dir()])
            date_folders = []
            for task_folder in task_folders:
                date_folders += sorted(
                    [e for e in task_folder.iterdir() if e.is_dir()])

            date_rows = [
                {'id': i,
                 'experiment': e.parent.name,
                 'experimentCN': TASK_NAME_EN2CN.get(e.parent.name, e.parent.name),
                 'datetime': e.name}
                for i, e in enumerate(date_folders)]

            for row in date_rows:
                cn = row['experimentCN']
                exp = [e for e in EXP.experiments if e['cn'] == cn]
                if not exp:
                    row['experimentType'] = '--'
                if len(exp) > 0:
                    exp = exp[0]
                    row['experimentType'] = exp['type'][0]

            date_table.update_rows(date_rows)
            date_table.on('row-click', self._date_table_on_row_click)

    Analysis()

    return


async def start_computing(evt, compute, on_start: callable, on_finish: callable):
    on_start()

    cwd = compute.cwd
    mname = compute.mname
    args = compute.args
    script = compute.script
    commands = ['python', script.as_posix()] + args

    cwd.mkdir(exist_ok=True, parents=True)

    # Delete existing files
    _finish = cwd / f'{mname}.finish'
    if _finish.is_file():
        _finish.unlink()

    _error = cwd / f'{mname}.error'
    if _error.is_file():
        _error.unlink()

    # Actually running the experiment
    _stdout = open(cwd / f'{mname}.stdout', 'w', encoding=ENCODING)
    _stderr = open(cwd / f'{mname}.stderr', 'w', encoding=ENCODING)
    try:
        ui.notify(f'计算开始：{mname=}，{commands=}', **NOTIFY_KWARGS.positive)
        await asyncio.sleep(0.1)

        # 在线程池中运行同步的 subprocess.run
        result = await asyncio.to_thread(
            subprocess.run,
            commands,
            cwd=cwd,
            stdout=_stdout,
            stderr=_stderr,
            encoding=ENCODING,
            env={**os.environ, 'PYTHONIOENCODING': ENCODING}
        )

        # 等待进程完成
        assert result.returncode == 0, '执行完毕但 returncode 不为 0。'
        print(result, file=open(_finish, 'w', encoding=ENCODING))

        logger.info(f'feature_processing finished: {commands=}')
        ui.notify(f'计算完成：{mname=}，{commands=}', **NOTIFY_KWARGS.positive)
        await asyncio.sleep(0.1)

    except Exception as err:
        logger.error(f'{mname} failed: {err=}')
        with open(_error, 'w', encoding=ENCODING) as file:
            file.write(f'{err=}\r\n')
            import traceback
            file.write(traceback.format_exc())
        ui.notify(f'特征分析（{mname}）中遇到错误：{err=}', **NOTIFY_KWARGS.negative)

    on_finish()
    return


async def start_preprocessing(evt, script: Path, cwd: Path, args1: list, args2: list, on_start: callable, on_finish: callable):
    on_start()

    commands = [
        'python', script.absolute().as_posix(),
    ] + args1 + args2

    (cwd / 'preprocessing').mkdir(exist_ok=True, parents=True)

    # Delete existing files
    _finish = cwd / 'preprocessing.finish'
    if _finish.is_file():
        _finish.unlink()

    _error = cwd / 'preprocessing.error'
    if _error.is_file():
        _error.unlink()

    # Actually running the experiment
    _stdout = open(cwd / 'preprocessing.stdout', 'w', encoding=ENCODING)
    _stderr = open(cwd / 'preprocessing.stderr', 'w', encoding=ENCODING)
    try:
        ui.notify(f'预处理开始：{commands=}', **NOTIFY_KWARGS.positive)
        await asyncio.sleep(0.1)

        # 在线程池中运行同步的 subprocess.run
        result = await asyncio.to_thread(
            subprocess.run,
            commands,
            cwd=cwd,
            stdout=_stdout,
            stderr=_stderr,
            encoding=ENCODING,
            env={**os.environ, 'PYTHONIOENCODING': ENCODING}
        )

        # 等待进程完成
        assert result.returncode == 0, '执行完毕但 returncode 不为 0。'
        print(result, file=open(_finish, 'w', encoding=ENCODING))

        logger.info(f'Preprocessing finished: {commands=}')
        ui.notify(f'预处理完成：{commands=}', **NOTIFY_KWARGS.positive)
        await asyncio.sleep(0.1)

    except Exception as err:
        logger.exception(err)
        logger.error(f'Preprocessing failed: {err=}')
        with open(_error, 'w', encoding=ENCODING) as file:
            file.write(f'{err=}\r\n')
            import traceback
            file.write(traceback.format_exc())
        ui.notify(f'预处理过程中遇到错误：{err=}', **NOTIFY_KWARGS.negative)

    await asyncio.sleep(0.1)
    on_finish()
    await asyncio.sleep(0.1)

    return
