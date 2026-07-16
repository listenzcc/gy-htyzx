import pandas as pd
from nicegui import ui


def date_input(name, value: str):
    inp = ui.input(
        name,
        value=value
    ).props('readonly')

    def open_dialog():
        dialog.open()

    with ui.dialog() as dialog:
        with ui.card():
            date = ui.date(value)

            def apply_date():
                inp.value = date.value
                dialog.close()

            ui.button('Apply', on_click=apply_date)

    inp.on('click', open_dialog)
    return inp


def image_select(image_files: dict, label: str = 'Image'):
    # image_files: Path: name
    # on select, put the image onto the img

    # Fetch the first path and name
    for path, name in image_files.items():
        break

    select = ui.select(options=image_files, label=label, value=path)
    img = ui.image().bind_source_from(select, 'value')

    # def set_image(value):
    #     print(value, img)
    #     img.source = value
    #     img.update()  # 刷新显示

    # img = ui.image(path)


def image_table_txt_select(files: dict, label: str = '多功能文件查看器'):
    if not files:
        return

    for path, name in files.items():
        break

    with ui.card().classes('w-full'):
        select = ui.select(options=files, label=label,
                           value=path, on_change=lambda: _on_change()).classes('w-full')
        img = ui.image().bind_source_from(select, 'value').classes('w-full')
        row = ui.row().classes('w-full')

    def _on_change():
        img.set_visibility(False)
        row.clear()

        if select.value.name.endswith('.csv'):
            df = pd.read_csv(select.value)
            with row:
                ui.table.from_pandas(df).classes(
                    'max-h-[28em] overflow-scroll w-full')
        elif select.value.name.endswith('.json'):
            df = pd.read_json(select.value)
            with row:
                ui.table.from_pandas(df).classes(
                    'max-h-[28em] overflow-scroll w-full')
        elif select.value.name.endswith('.png'):
            img.set_visibility(True)
        elif select.value.name.endswith('.cnt'):
            with row:
                ui.label('.cnt 是脑电文件，该文件无法打印')
        else:
            try:
                content = open(select.value, encoding='utf-8').read()
            except Exception as err:
                content = f'无法解析该文件：{err}'
            with row:
                ui.textarea(label=select.value.as_posix(),
                            value=content).classes('w-full')

    _on_change()
    return
