from nicegui import ui


def debug_block(content, language='python'):
    with ui.expansion('Debug Information', icon='bug_report').classes('w-full mx-auto mt-4 text-blue-500'):
        ui.code(content, language=language).classes('w-full')
