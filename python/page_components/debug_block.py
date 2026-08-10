import sys
from nicegui import ui

# ------------------------------------------------------------------------------
sys.path.append('..')  # noqa
from constants import *


def debug_block(content, language='python'):
    if not ALLOW_DEBUG_INFO_DISPLAY:
        return

    with ui.expansion('Debug Information', icon='bug_report').classes('w-full mx-auto mt-4 text-blue-500'):
        ui.code(content, language=language).classes('w-full')
