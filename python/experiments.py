from pathlib import Path
from collections import defaultdict

folders = [
    './experiments/script',
    './experiments/script/模拟任务',
    './experiments/script/认知能力测试',
    './experiments/script/认知训练',
]

experiments = []

options_replacement_map = {
    '-': '',
    ',': ' ',
    ':': ' ',
}


def parse_options(options):
    use_none_as_default = False
    formulated_options = []
    for opt in options:
        content = opt.strip()

        try:
            # Check if use none as default for future options
            if content == '# 以下不是必须参数，提供默认值即可':
                use_none_as_default = True
                formulated_options.append(
                    {'type': 'mention', 'content': content, 'level': 'info'})
                continue

            if not content.startswith('-'):
                formulated_options.append(
                    {'type': 'mention', 'content': content, 'level': 'warning'})
                continue

            for k, v in options_replacement_map.items():
                content = content.replace(k, v)
            parts = [e.strip()
                     for e in content.split() if e.strip()]

            _name = parts[0]
            _type = parts[1]

            if _type == 'int':
                formulated_options.append({
                    'name': _name,
                    'type': _type,
                    'min': int(parts[2]),
                    'max': int(parts[3]),
                    'step': 1,
                    'value': None if use_none_as_default else int(parts[2])
                })
            elif _type == 'float':
                formulated_options.append({
                    'name': _name,
                    'type': _type,
                    'min': float(parts[2]),
                    'max': float(parts[3]),
                    'step': (float(parts[3]) - float(parts[2])) / 10,
                    'value': None if use_none_as_default else float(parts[2])
                })
            elif _type == 'option':
                formulated_options.append({
                    'name': _name,
                    'type': _type,
                    'options': parts[2:],
                    'value': None if use_none_as_default else parts[2]
                })
            else:
                formulated_options.append({
                    'type': 'mention',
                    'content': content
                })

        except Exception as err:
            formulated_options.append({
                'type': 'mention',
                'level': 'error',
                'content': f'{opt=}, {err=}'
            })

    return formulated_options


for folder in folders:
    for file in Path(folder).glob('*.py'):
        header = open(file, encoding='utf-8').read().split('"""')[1]
        items = header.split('@')[1:]

        fields = {'type': ['一般任务']}
        for item in items:
            if item.lower().startswith('abstract:'):
                fields['abstract'] = item.strip()
            if item.lower().startswith('type:'):
                fields['type'] = [e.strip()
                                  for e in item[len('type:'):].strip().split() if e.strip()]
            if item.lower().startswith('parameter:'):
                fields['options'] = [e.strip()
                                     for e in item[len('parameter:'):].split('\n') if e.strip()]

        fields.update({
            'script': file.as_posix(),
            'folder': folder,
            'file': file.name,
            'cn': file.stem,
        })

        experiments.append(fields)


class Experiments:
    experiments = experiments

    def __init__(self):
        self.detect_types()
        self.format_options()

    def detect_types(self):
        '''
        Detect task types.
        Now it only supports two levels types.

        yield self.type_dct to restore the task types.
        '''

        dct = defaultdict(set)
        for exp in self.experiments:
            types = exp['type']
            dct[types[0]]
            [dct[types[0]].add(e) for e in types[1:]]

        self.type_dct = dct

        return dct

    def format_options(self):
        '''
        Generate formatted_options.
        '''
        for exp in self.experiments:
            opts = parse_options(exp['options'])
            exp['has_mention'] = any(
                opt.get('type') == 'mention' for opt in opts)
            exp['formatted_options'] = opts
        return


if __name__ == '__main__':
    experiments = Experiments()

    from rich import print

    mention_experiments = dict()

    for exp in experiments.experiments:
        print('\n-------------------------------------------------------------')
        print(exp)
        for opt in exp['formatted_options']:
            if opt['type'] == 'mention':
                mention_experiments[exp['script']] = exp
            for k, v in opt.items():
                print(f'{k}: {v}')

    n = len(mention_experiments)

    for i, exp in enumerate(mention_experiments.values()):
        print(f'\n** {i+1} | {n} *********************************************')
        print(exp)
        for opt in exp['formatted_options']:
            for k, v in opt.items():
                print(f'{k}: {v}')

    from textual.app import App, ComposeResult, Binding
    from textual.containers import Container, ScrollableContainer
    from textual.widgets import Header, Footer, Label, ListView, ListItem, Static

    class ExperimentApp(App):
        BINDINGS = [
            Binding("a", "filter_all", "Filter all"),
            Binding("i", "filter_info", "Filter info"),
            Binding("w", "filter_warning", "Filter warning"),
            Binding("e", "filter_error", "Filter error"),
            Binding("m", "toggle_mention", "Toggle mention"),
            Binding("q", "request_quit", "Quit"),
        ]

        mention_only = True
        mention_level = ''

        def __init__(self, experiments):
            super().__init__()
            self.experiments = experiments
            self.selected_experiments = {}
            self.process_data()

        def _restore_focus(self):
            self.query_one("#experiment-list").focus()

        def action_request_quit(self):
            self.app.exit()

        def action_filter_all(self):
            self.mention_level = ''
            self._refresh()
            pass

        def action_filter_info(self):
            self.mention_level = 'info'
            self._refresh()
            pass

        def action_filter_warning(self):
            self.mention_level = 'warning'
            self._refresh()
            pass

        def action_filter_error(self):
            self.mention_level = 'error'
            self._refresh()
            pass

        def action_toggle_mention(self):
            self.mention_only = not self.mention_only
            self._refresh()

        def _refresh(self):
            # 重做数据
            self.process_data()
            # 完全重新构建界面
            self.refresh(recompose=True)
            self.call_after_refresh(self._restore_focus)

        def process_data(self):
            self.selected_experiments = {}
            level = self.mention_level
            for i, exp in enumerate(self.experiments.experiments):
                key = f'{i+1:03d} ' + exp["script"]
                if exp['has_mention']:
                    key = f'[yellow]{key}[/yellow]'

                for opt in exp["formatted_options"]:
                    if self.selected_experiments.get(key):
                        break
                    # Only consider mention option
                    if self.mention_only:
                        if opt.get("type") == "mention" and level in opt.get('level'):
                            self.selected_experiments[key] = exp
                    else:
                        self.selected_experiments[key] = exp

        def compose(self) -> ComposeResult:
            yield Header()

            with Container():
                yield Static(f"选择实验: {self.mention_only=} | {self.mention_level=}")

                yield ListView(
                    *[
                        ListItem(
                            Label(name),
                            name=name,  # 把实验名存这里
                        )
                        for name in self.selected_experiments
                    ],
                    id="experiment-list",
                )

            with ScrollableContainer(id="display-area"):
                yield Static("请选择实验", id="content")

            yield Footer()

        def on_list_view_selected(self, event: ListView.Selected) -> None:
            content = self.query_one("#content", Static)

            exp_name = event.item.name
            if exp_name is None:
                return

            exp = self.selected_experiments[exp_name]

            lines = [
                f"脚本: {exp['script']}",
                "-" * 40,
            ]

            for opt in exp["formatted_options"]:
                color = '#aaaaff'

                if opt['type'] == 'mention' and opt['level'] == 'error':
                    color = '#ff3030'

                if opt['type'] == 'mention' and opt['level'] == 'info':
                    color = '#00ff00'

                if opt['type'] == 'mention' and opt['level'] == 'warning':
                    color = '#ffff00'

                for k, v in opt.items():
                    lines.append(f"[{color}]{k}: {v}[/{color}]")
                lines.append("-" * 20)

            content.update("\n".join(lines))

    ExperimentApp(experiments).run()
