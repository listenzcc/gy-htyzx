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
