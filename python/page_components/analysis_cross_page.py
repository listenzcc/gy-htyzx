
# ------------------------------------------------------------------------------
import numpy as np
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

# ------------------------------------------------------------------------------
sys.path.append('..')  # noqa
from constants import *
from experiments import Experiments, TASK_NAME_EN2CN
from auth.user_service import UserService

# ------------------------------------------------------------------------------
# 设置全局默认模板
import plotly.io as pio
import plotly.express as px
# 或 'plotly', 'ggplot2', 'seaborn', 'simple_white', 'plotly_dark'
pio.templates.default = 'ggplot2'


# ------------------------------------------------------------------------------
logger.add("log/analysis_{time:YYYY-MM-DD}.log",
           encoding=ENCODING, rotation='1 day')

# ------------------------------------------------------------------------------
EXP = Experiments()

# ------------------------------------------------------------------------------
DATA_FOLDER = Path('./data')


# ------------------------------------------------------------------------------
def render_analysis_cross_page(id: int, uuid: str, user_service: UserService, user_ids: list = []):

    def has_permission():
        return user_service.get_user_by_id(id).has_permission('analysis_cross')

    def fetch_users():
        all_users = sorted(user_service.list_users(), key=lambda e: e.id)
        selected_users = [
            e for e in all_users if not user_ids or e.id in user_ids]
        good_users = [e for e in selected_users if (
            DATA_FOLDER / e.uuid).is_dir()]
        return good_users

    def taskEN2CN(en):
        return TASK_NAME_EN2CN.get(en, en)

    if not has_permission():
        ui.label('Permission deny').classes(STYLES.errorText)
        return

    # --------------------------------------------------------------------------
    # Walk thought the data folder for the large_table
    users = fetch_users()
    uuid_table = {e.uuid: e.username for e in users}
    uuid_folders = [e for e in DATA_FOLDER.iterdir() if e.is_dir()
                    and e.name in uuid_table]
    array = []
    for ufolder in uuid_folders:
        task_folders = [e for e in ufolder.iterdir() if e.is_dir()]
        username = uuid_table[ufolder.name]
        for tfolder in task_folders:
            date_folders = [e for e in tfolder.iterdir() if e.is_dir()]
            task = tfolder.name
            task_cn = taskEN2CN(task)
            task_type = EXP.cn2type_dct[task_cn]
            for dfolder in date_folders:
                csv = sorted(dfolder.glob('*.csv'))
                if not csv:
                    continue
                csv = csv[0]
                array.append(
                    {'username': username, 'datestr': dfolder.name, 'task': task, 'taskCN': task_cn, 'taskType': task_type, 'csv': csv})
    large_table = pd.DataFrame(array)

    with ui.card().classes(STYLES.fullCard):
        ui.table.from_pandas(
            large_table, pagination={'rowsPerPage': 10}).classes('w-full')

    # --------------------------------------------------------------------------
    # Select task
    tasks = large_table['taskCN'].unique().tolist()
    task_select = ui.select(tasks, label='选择要分析的任务').classes('w-full')
    task_example_card = ui.card().classes('w-full')
    task_select.on_value_change(lambda: _on_taskCN_select())

    def _better_csv(csv):
        lst = [f'{e}'.lower() for e in csv[csv.columns[0]].tolist()]
        flag = False
        if 'summary' in lst:
            i = lst.index('summary')
            csv = csv.iloc[i+1:][csv.columns[:2]]
            csv.columns = ['name', 'value']
            flag = True
        return csv, flag

    def _on_taskCN_select():
        selected_task_df = large_table.query(
            f'taskCN == "{task_select.value}"')
        csv, flag = _better_csv(pd.read_csv(selected_task_df.iloc[0]['csv']))

        task_example_card.clear()
        with task_example_card:
            ui.label('数据报告样例').classes(STYLES.cardSubTitleLabel)
            ui.table.from_pandas(csv).classes(
                'w-full max-h-[28em] overflow-scroll')

            if not flag:
                ui.label(f'该任务不满足交叉分析条件').classes(STYLES.errorText)
                return

            # Collect all the summary
            _dfs = []
            for _, row in selected_task_df.iterrows():
                csv, flag = _better_csv(pd.read_csv(row['csv']))
                if flag:
                    csv['date'] = datetime.strptime(
                        row['datestr'], FILE_DATE_FMT)
                    csv['username'] = row['username']
                    _dfs.append(csv)
            _summary_df = pd.concat(_dfs)
            ui.label(f'该任务包括这些受试者的数据').classes(STYLES.cardSubTitleLabel)
            ui.label('，'.join(_summary_df['username'].unique()))

            # Make UI
            value_name_select = ui.select(
                csv[csv.columns[0]].tolist(),
                label='选择项目名进行交叉分析'
            ).classes('w-full')

            value_name_select.on_value_change(lambda: _on_value_name_select())
            _plotly_row = ui.row().classes('w-full justify-center')

            def _on_value_name_select():
                name = value_name_select.value
                _df = _summary_df.query(f'name=="{name}"').copy()
                _df['value'] += np.random.random(len(_df))
                fig = px.line(_df, x='date', y='value',
                              color='username', markers=True)
                _plotly_row.clear()
                with _plotly_row:
                    ui.plotly(fig)

    return
