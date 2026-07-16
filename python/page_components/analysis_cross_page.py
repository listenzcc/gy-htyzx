
# ------------------------------------------------------------------------------
from collections import defaultdict
import numpy as np
import pandas as pd
import os
import sys
import shutil
import asyncio
import subprocess
from scipy import stats
from loguru import logger
from pathlib import Path
from nicegui import ui, events
from datetime import datetime

# ------------------------------------------------------------------------------
sys.path.append('..')  # noqa
from constants import *
from experiments import Experiments, TASK_NAME_EN2CN, EEG_SCRIPT_SUFFIX_EN2CN
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
FEATURE_NAMES = {
    'conn': EEG_SCRIPT_SUFFIX_EN2CN['conn'],
    'erp': EEG_SCRIPT_SUFFIX_EN2CN['erp'],
    'psd': EEG_SCRIPT_SUFFIX_EN2CN['psd'],
    'ersp': EEG_SCRIPT_SUFFIX_EN2CN['ersp']
}


# ------------------------------------------------------------------------------
def correlation_with_pvalue(x, y):
    corr, p_value = stats.pearsonr(x, y)
    return pd.Series({
        'correlation': corr,
        'p_value': p_value,
        'significant': p_value < 0.05
    })


# ------------------------------------------------------------------------------
def find_csv(folder: Path, feat: str = ''):
    try:
        if feat == 'conn':
            csv = pd.read_csv(
                next(folder.glob('*_roi_connectivity.csv')), index_col=0)
        elif feat == 'ersp':
            csv = pd.read_csv(next(folder.glob('itc_features.csv')))
        else:
            csv = pd.read_csv(next(folder.glob('*.csv')))
        return csv
    except:
        return


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

    with ui.card().classes('w-full'):
        _df = large_table[['username', 'datestr', 'taskCN', 'taskType']].copy()
        _df.columns = ['用户名', '日期', '任务名', '任务类型']
        ui.table.from_pandas(
            _df, pagination={'rowsPerPage': 5}).classes('w-full')

    # --------------------------------------------------------------------------
    # Select task
    tasks = large_table['taskCN'].unique().tolist()
    task_select = ui.select(tasks, label='选择要分析的任务').classes('w-full')
    task_example_card = ui.card().classes(STYLES.fullCard)
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
            ui.table.from_pandas(csv, pagination={'rowsPerPage': 5}).classes(
                'w-full max-h-[28em] overflow-scroll')

            if not flag:
                ui.label(f'该任务不满足交叉分析条件').classes(STYLES.errorText)
                return

            # Collect all the summary
            _dfs = []

            _eeg_feature_collection = defaultdict(list)
            _eeg_feature_errors = defaultdict(list)

            for _, row in selected_task_df.iterrows():
                csv, flag = _better_csv(pd.read_csv(row['csv']))
                if flag:
                    csv['date'] = datetime.strptime(
                        row['datestr'], FILE_DATE_FMT)
                    csv['username'] = row['username']
                    _dfs.append(csv)
                    _folder = Path(row['csv']).parent
                    for _feat, _feat_cn in FEATURE_NAMES.items():
                        __folder = _folder / _feat
                        _csv = find_csv(__folder, _feat)
                        if _csv is None:
                            _eeg_feature_errors[_feat].append(
                                f'缺少数据：{csv["username"]} | {__folder}')
                            continue
                        _eeg_feature_collection[_feat].append(
                            (row['username'], row['datestr'], _csv))

            _summary_df = pd.concat(_dfs)
            ui.label(f'该任务包括这些受试者的数据').classes(STYLES.cardSubTitleLabel)
            ui.label('，'.join(_summary_df['username'].unique()))

            # Make UI
            value_name_select = ui.select(
                csv[csv.columns[0]].tolist(),
                label='选择任务统计值进行交叉分析'
            ).classes('w-full')

            cross_values = {
                'task_df': None,
                'eeg_df': None
            }

            value_name_select.on_value_change(lambda: _on_value_name_select())

            _task_result_card = ui.card().classes('w-full')

            def _on_value_name_select():
                name = value_name_select.value
                _df = _summary_df.query(f'name=="{name}"').copy()
                _df['value'] += np.random.random(len(_df))
                fig = px.line(_df, x='date', y='value',
                              color='username', markers=True)

                cross_values['task_df'] = _df.copy()

                _task_result_card.clear()
                with _task_result_card:
                    with ui.row().classes('w-full justify-evenly'):
                        ui.label('按用户的时间序列图').classes(STYLES.cardSubTitleLabel)
                    _plotly_row = ui.row().classes('w-full justify-center')

                    with ui.row().classes('w-full justify-evenly'):
                        ui.label('按用户的分类统计表').classes(STYLES.cardSubTitleLabel)
                    _agg_row = ui.row().classes('w-full justify-center')

                _plotly_row.clear()
                with _plotly_row:
                    ui.plotly(fig)

                _agg_row.clear()
                with _agg_row:
                    ui.table.from_pandas(_df, pagination={'rowsPerPage': 5})
                    __df = _df.groupby('username')['value'].agg(
                        ['mean', 'median', 'std']).reset_index()
                    ui.table.from_pandas(__df)
                return

            ui.separator()
            ui.label('与脑电数据的联合分析').classes(STYLES.cardSubTitleLabel)
            _with_eeg_analysis_row = ui.row().classes('w-full justify-center')
            with _with_eeg_analysis_row:
                feat_select = ui.select(label='选择要分析的脑电特征',
                                        options=list(FEATURE_NAMES.keys())).classes('w-full')
                feat_detail_textarea = ui.textarea(
                    label='脑电特征参数').classes('w-full h-[10em]')
                feat_results_card = ui.card().classes('w-full')

            feat_select.on_value_change(lambda: _feat_select_on_change())

            def _feat_select_on_change():
                _feat = feat_select.value
                feat_results_card.clear()

                _errors = _eeg_feature_errors.get(_feat)
                if _errors:
                    with feat_results_card:
                        ui.label(f'{_errors}').classes(STYLES.errorText)
                    return

                _eeg_results = _eeg_feature_collection.get(_feat)
                if _eeg_results is None:
                    with feat_results_card:
                        ui.label(f'没有找到对应的特征数据').classes(STYLES.errorText)
                    return

                if _feat == 'conn':
                    feat_detail_textarea.value = 'Frontal Parietal'
                    _c, _i = 'Frontal', 'Parietal'
                elif _feat == 'psd':
                    feat_detail_textarea.value = 'Delta_PSD 0'
                    _c, _i = 'Delta_PSD', 0
                elif _feat == 'ersp':
                    feat_detail_textarea.value = 'ITC_P2_Delta 0'
                    _c, _i = 'ITC_P2_delta', 0
                elif _feat == 'erp':
                    feat_detail_textarea.value = 'P2_Amplitude 0'
                    _c, _i = 'P2_Amplitude', 0

                _dfs = []
                for username, datestr, _df in _eeg_results:
                    _dfs.append({
                        'username': username,
                        'date': datetime.strptime(datestr, FILE_DATE_FMT),
                        'value': _df[_c][_i]})
                _df = pd.DataFrame(_dfs)
                _df['name'] = _feat
                _df['value'] *= (np.random.random(len(_df)) + 1)
                fig = px.line(_df, x='date', y='value',
                              color='username', markers=True)
                with feat_results_card:
                    with ui.row().classes('w-full justify-evenly'):
                        ui.label('按用户的脑电特征图').classes(STYLES.cardSubTitleLabel)
                    with ui.row().classes('w-full justify-evenly'):
                        ui.plotly(fig)
                    with ui.row().classes('w-full justify-evenly'):
                        ui.label('按用户的脑电特征表').classes(STYLES.cardSubTitleLabel)
                    with ui.row().classes('w-full justify-evenly'):
                        ui.table.from_pandas(
                            _df, pagination={'rowsPerPage': 5})
                        __df = _df.groupby('username')['value'].agg(
                            ['mean', 'median', 'std']).reset_index()
                        ui.table.from_pandas(__df)

                    _task_df = cross_values.get('task_df')
                    if _task_df is None:
                        ui.label('请选择参与分析的任务统计值').classes(STYLES.errorText)
                        return

                    merged_df = pd.merge(_task_df, _df, on=[
                                         'username', 'date'])

                    result = merged_df.groupby('username').apply(
                        lambda x: correlation_with_pvalue(
                            x['value_x'], x['value_y'])
                    ).reset_index()

                    with ui.row().classes('w-full justify-evenly'):
                        ui.label('交叉分析结果').classes(STYLES.cardSubTitleLabel)
                    with ui.row().classes('w-full justify-evenly'):
                        ui.table.from_pandas(result)

                return

    return
