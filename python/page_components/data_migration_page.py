import os
import sys
import time
import shutil
import asyncio
import threading
import subprocess
import pandas as pd

from typing import List
from loguru import logger
from nicegui import ui
from pathlib import Path
from datetime import datetime

from .inputs import date_input, image_select

sys.path.append('..')  # noqa
from constants import *
from auth.user_service import UserService, User, or_

# ------------------------------------------------------------------------------
logger.add("log/data_migratation_{time:YYYY-MM-DD}.log",
           encoding=ENCODING, rotation='1 day')


def build_tree(path, max_depth=None, current_depth=0):
    """
    递归构建文件树结构
    """
    # It reaches the max_depth, list all the files
    if max_depth is not None and current_depth >= max_depth:
        children = [{'id': e} for e in sorted(
            [e.relative_to(path).as_posix() for e in path.rglob('*')])]
        return children

    path = Path(path)
    if not path.is_dir():
        return None

    children = []
    for item in sorted(path.iterdir()):
        if item.is_dir():
            child_tree = build_tree(item, max_depth, current_depth + 1)
            if child_tree is not None:
                children.append({
                    'id': item.name,
                    'children': child_tree
                })
        else:
            children.append({'id': item.name})

    return children


def data_migration_export(id: int, user_service: UserService):
    def _check_permission():
        return user_service.get_user_by_id(id).has_permission('export_users')

    with ui.card().classes(STYLES.fullCard):
        ui.label('导出用户及对应的数据').classes(STYLES.cardTitleLabel)

        # Check permission
        if not _check_permission():
            ui.label('无 export_users 权限或用户已被禁用').classes(STYLES.errorText)
            return

        # Check export
        filename = Path('export/users_export.csv')
        if not filename.is_file():
            ui.label(f'没有找到导出的用户列表：{filename=}').classes(STYLES.errorText)
            return

        # Exporting steps
        # 1. Show the table
        with ui.card().classes(STYLES.fullCard):
            ui.label(f'1.导出的用户信息表：{filename.as_posix()}')
            df = pd.read_csv(filename, encoding='utf-8-sig')
            ui.table.from_pandas(df).classes(STYLES.pandasTable)

        # 2. Show the data
        with ui.card().classes(STYLES.fullCard):
            ui.label(f'2.涉及的实验数据')
            data_folder = Path('data')
            uuids = df['uuid'].to_list()

            # Folders' path is $uuid/$taskname/$datetime
            folders = sorted(
                [e for e in data_folder.iterdir() if e.name in uuids])

            tree_data = [{
                'id': folder.name,
                'username': df[df['uuid'] == folder.name].iloc[0]['username'],
                'children': build_tree(folder, 2)
            } for folder in folders]

            for uuid_data in tree_data:
                ui.separator()
                ui.label(f"用户名：{uuid_data['username']}").classes(
                    STYLES.infoText)
                ui.tree([uuid_data], label_key='id').classes(
                    'w-full max-h-[28em] overflow-y-scroll')

        # 3. Package these data
        with ui.card().classes(STYLES.fullCard):
            ui.label(f'3. 打包这些数据')

            output_dir = filename.with_name('data_export')
            example_rename_output_dir = filename.with_name(
                f'data_export_{datetime.strftime(datetime.now(), FILE_DATE_FMT)}')
            ui.label(f'这些数据将被打包存储在以下位置：{output_dir.as_posix()}')
            if output_dir.is_dir():
                ui.label(f'但 {output_dir.as_posix()} 已存在，如果它是您打包的正确数据，那么无须再次打包。如果再次打包，它将按时间规则被重命名，例如 {example_rename_output_dir.as_posix()}').classes(
                    STYLES.attentionText)

            ui.button('开始打包',
                      on_click=lambda evt: package_data(
                          _check_permission, evt, folders, output_dir, packing_progress, finish_label, error_label))

            # progress_bar
            packing_progress = ui.linear_progress()

            # finish label
            finish_label = ui.label().classes(STYLES.infoText)
            error_label = ui.label().classes(STYLES.errorText)

    pass


async def package_data(cp_method, event, src_folders: List[Path], output_dir: Path, progress_bar, label, elabel):
    btn = event.sender

    try:
        # Check permission first
        assert cp_method(), 'Permission deny'

        btn.disable()

        progress_state = {'value': 0.0, 'msg': '--'}
        progress_bar.bind_value(progress_state, 'value')
        label.bind_text(progress_state, 'msg')

        if output_dir.is_dir():
            bak_output_dir = output_dir.with_name(
                '_'.join([output_dir.name, datetime.strftime(datetime.now(), FILE_DATE_FMT)]))
            output_dir.rename(bak_output_dir)
            logger.warning(
                f'Rename existing dir: {output_dir} -> {bak_output_dir}')

        output_dir.mkdir(exist_ok=True, parents=True)

        # Copy src_folders into output_dir
        # 统计总文件数（用于进度）
        total_files = 0
        for src in src_folders:
            if src.is_dir():
                total_files += sum(1 for _ in src.rglob('*') if _.is_file())
            else:
                total_files += 1

        copied_files = 0

        # 复制文件
        for src in src_folders:
            if src.is_dir():
                for file in src.rglob('*'):
                    if file.is_file():
                        rel_path = file.relative_to(src)
                        dst_file = output_dir / src.name / rel_path
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        progress_state['msg'] = rel_path.as_posix()
                        shutil.copy2(file, dst_file)

                        copied_files += 1
                        if total_files > 0:
                            progress_state['value'] = copied_files / \
                                total_files
                            await asyncio.sleep(0)
            else:
                dst_file = output_dir / src.name
                progress_state['msg'] = src.as_posix()
                shutil.copy2(src, dst_file)
                copied_files += 1
                if total_files > 0:
                    progress_state['value'] = copied_files / total_files
                    await asyncio.sleep(0)

        msg = f'Package data {[e.as_posix() for e in src_folders]} -> {output_dir.as_posix()}'
        logger.info(msg)
        ui.notify(msg, **NOTIFY_KWARGS.positive)
        label.text = f'打包完成（文件数量{total_files}），数据保存在：{output_dir.as_posix()}'

    except Exception as err:
        msg = f'Failed packing data: {err}'
        logger.error(msg)
        ui.notify(msg, **NOTIFY_KWARGS.negative)
        elabel.text = f'打包过程中出现异常：{err}'

    finally:
        btn.enable()

    return


def data_migration_import(id: int, user_service: UserService):
    def _check_permission():
        return user_service.get_user_by_id(id).has_permission('import_users')

    with ui.card().classes(STYLES.fullCard):
        ui.label('导入用户及对应的数据').classes(STYLES.cardTitleLabel)

        # Check permission
        if not _check_permission():
            ui.label('无 import_users 权限或用户已被禁用').classes(STYLES.errorText)
            return

        # 1. 选择待导入的数据目录
        with ui.card().classes(STYLES.fullCard):
            ui.label('1.选择待导入的数据目录')
            ui.label('该目录应该包含自动生成的用户信息文件 users_export.csv 和打包的实验数据 data_export').classes(
                STYLES.attentionText)

            with ui.row().classes('w-full'):
                import_data_dir = Path('./import')
                import_data_dir_input = ui.input(
                    '目录', value=import_data_dir.as_posix())
                contains = ui.list().props('dense separator')

        # 2. Display local users
        with ui.card().classes(STYLES.fullCard):
            ui.label('2.检查本地与导入用户')

            with ui.card().classes(STYLES.fullCard):
                ui.label('2.1与本地用户有冲突的导入用户，导入后这些用户将保留本地信息').classes(
                    STYLES.attentionText)
                list_with_conflict = ui.list().props(
                    'dense separator').classes('max-h-[28em] w-full overflow-scroll')
                with list_with_conflict:
                    ui.label('-')

            with ui.card().classes(STYLES.fullCard):
                ui.label('2.2与本地用户无冲突的导入用户，导入后这些用户将使用导入的信息').classes(
                    STYLES.infoText)
                list_without_conflict = ui.list().props(
                    'dense separator').classes('max-h-[28em] w-full overflow-scroll')
                with list_without_conflict:
                    ui.label('-')

        # 3. Submit importing
        with ui.card().classes(STYLES.fullCard):
            ui.label('3.确认导入用户和数据')
            importing_btn = ui.button('确认导入用户和数据')

            # progress_bar
            copying_progress = ui.linear_progress()

            # finish label
            finish_label = ui.label().classes(STYLES.infoText)
            error_label = ui.label().classes(STYLES.errorText)

        class Importing:
            def __init__(self):
                import_data_dir.mkdir(exist_ok=True, parents=True)
                import_data_dir_input.on_value_change(self._on_change_dir)
                import_data_dir_input.on('keydown.enter', self._on_change_dir)
                self._on_change_dir()

            def _on_change_dir(self):
                global import_data_dir
                import_data_dir = Path(import_data_dir_input.value)

                contains.clear()
                list_with_conflict.clear()
                list_without_conflict.clear()

                with contains:
                    importing_btn.disable()
                    if not import_data_dir.is_dir():
                        ui.item('目录不合法或不存在').classes(STYLES.errorText)
                        return

                    if not (import_data_dir / 'users_export.csv').is_file():
                        ui.item('目录不合法或不存在').classes(STYLES.errorText)
                        for p in sorted(import_data_dir.iterdir()):
                            ui.item(p.name).classes(STYLES.errorText)
                        return

                    ui.item('目录合法').classes(STYLES.infoText)
                    subs = sorted(import_data_dir.iterdir())
                    for i, path in enumerate(subs):
                        ui.item(
                            f'{i+1}/{len(subs)} | {"File" if path.is_file() else "Folder"} | {path.relative_to(import_data_dir).as_posix()}').classes(STYLES.infoText)

                    importing_btn.enable()

                df = pd.read_csv(import_data_dir /
                                 'users_export.csv', encoding='utf-8-sig')

                print(df)

                # Separate the usernames for with- and without-conflict
                new_user_rows = []

                # Mapping {importing-uuid: local-uuid}
                uuid_map = {}
                for i, row in df.iterrows():
                    # row is importing user record
                    # Check if local already has the user with username
                    # If so, use the local uuid
                    # Otherwise, add the new user
                    # Notice that the importing user may has the repeated uuid with local
                    # So, re-gen uuid for every new user

                    username = row['username']

                    user = user_service.get_user_by_username(username)

                    if user:
                        uuid_map[row['uuid']] = user.uuid
                        with list_with_conflict:
                            ui.item(username)
                            ui.item(f'{user.to_dict()}')
                    else:
                        new_uuid = user_service.gen_uuid()
                        uuid_map[row['uuid']] = new_uuid
                        new_user_rows.append((row, new_uuid))
                        with list_without_conflict:
                            ui.item(username)
                            ui.item(f'{row.to_dict()}')

                async def _copy_files():
                    # If folder does not exist, do nothing and quit.
                    output_dir = Path('./data')
                    import_dir = import_data_dir / 'data_export'
                    print(import_dir, import_dir.is_dir())
                    if not import_dir.is_dir():
                        return

                    coping_status = {'text': '', 'num': 0}
                    finish_label.bind_text(coping_status, 'text')
                    copying_progress.bind_value(coping_status, 'value')

                    # Copy files
                    total = len(
                        list([e for e in import_dir.rglob('*') if not e.is_dir()]))
                    num = 0
                    for uuid_folder in [e for e in import_dir.iterdir() if e.is_dir()]:
                        # Translate it into local uuid
                        uuid = uuid_map.get(uuid_folder.name, uuid_folder.name)

                        for task_folder in [e for e in uuid_folder.iterdir() if e.is_dir()]:
                            task = task_folder.name
                            for date_folder in [e for e in task_folder.iterdir() if e.is_dir()]:
                                date_str = date_folder.name
                                src = date_folder
                                dst = output_dir / uuid / task / date_str
                                if dst.is_dir():
                                    i = 0
                                    while dst.is_dir():
                                        i += 1
                                        dst = output_dir / uuid / \
                                            task / (date_str + f'.{i}')
                                print(f'{src} -> {dst}')
                                for _src in src.rglob('*'):
                                    _dst = dst / _src.relative_to(src)
                                    _dst.parent.mkdir(
                                        exist_ok=True, parents=True)
                                    if _src.is_dir():
                                        continue
                                    shutil.copy2(_src, _dst)
                                    num += 1
                                    coping_status['text'] = _src.as_posix()
                                    coping_status['value'] = num / total
                                    await asyncio.sleep(0)
                    coping_status['text'] = f'导入完成（文件数量{total}）'
                    coping_status['value'] = 1

                def _importing_users():
                    '''Import users'''
                    for row, new_uuid in new_user_rows:
                        kwargs = dict(
                            # Use the new uuid, if (and always if) it has mapping
                            uuid=new_uuid,  # origin is row['uuid']
                            username=row['username'],
                            password=row['password_hash'],
                            do_not_generate_hash=True,
                            role=row['role'],
                            gender=row['gender'],
                            education=row['education'],
                            is_active=row['is_active'],
                            birth_date=datetime.strptime(
                                row['birth_date'], DATE_FMT) if row['birth_date'] else None,
                            training_date=datetime.strptime(
                                row['training_date'], DATE_FMT) if row['training_date'] else None,
                        )
                        user = user_service.create_user(**kwargs)
                        logger.info(f'Imported {user.to_dict()}')

                async def _importing_btn_on_click():
                    try:
                        _importing_users()
                    except Exception as err:
                        ui.notify(f'导入用户时遇到错误：{err}', **NOTIFY_KWARGS.negative)

                    await _copy_files()

                importing_btn.on_click(_importing_btn_on_click)

                pass

        importing = Importing()

    pass
