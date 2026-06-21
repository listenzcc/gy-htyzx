from nicegui import ui


def date_input(name, value):
    inp = ui.input(
        name,
        value=value if isinstance(value, str) else ''
    ).props('readonly')

    def open_dialog():
        dialog.open()

    with ui.dialog() as dialog:
        with ui.card():
            date = ui.date()

            def apply_date():
                inp.value = date.value
                dialog.close()

            ui.button('Apply', on_click=apply_date)

    inp.on('click', open_dialog)
    return inp
