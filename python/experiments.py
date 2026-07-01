from pathlib import Path

folders = [
    './experiments/script',
    './experiments/script/模拟任务',
    './experiments/script/认知能力测试',
    './experiments/script/认知训练',
]

experiments = [
    # {'script': './experiments/script/单音节分辨.py'},
    # {'script': './experiments/script/模拟任务/单音节分辨_信号灯2.py'}
]

for folder in folders:
    for file in Path(folder).glob('*.py'):
        experiments.append(
            {'script': file.as_posix(),
             'folder': folder,
             'file': file.name,
             'cn': file.stem,
             'abstract': open(file, encoding='utf-8').read().split('"""')[1].strip()
             })


class Experiments:
    experiments = experiments

    def __init__(self):
        # self.load_experiments()
        pass

    # def load_experiments(self):
    #     for exp in self.experiments:
    #         exp['cn'] = Path(exp['script']).stem
    #         exp['abstract'] = open(
    #             exp['script'], encoding='utf-8').read().split('"""')[1].strip()
    #     pass
