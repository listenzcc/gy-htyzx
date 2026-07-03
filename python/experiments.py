from pathlib import Path
from collections import defaultdict

folders = [
    './experiments/script',
    './experiments/script/模拟任务',
    './experiments/script/模拟任务1',
    './experiments/script/认知能力测试',
    './experiments/script/认知训练',
]

experiments = []

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
        self.type_dct = self.detect_types()
        pass

    def detect_types(self):
        dct = defaultdict(set)
        for exp in self.experiments:
            types = exp['type']
            dct[types[0]].add('.')
            [dct[types[0]].add(e) for e in types[1:]]
        return dct
