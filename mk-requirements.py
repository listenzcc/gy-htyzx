import mne
import mne_connectivity
import rich
import antio
import plotly
import sklearn
import loguru
import pandas
import textual
import fastapi
import nicegui
import psychopy
import werkzeug
import starlette
import omegaconf
import sqlalchemy
import latex2mathml

import importlib.metadata


lst = ['# python==3.11.15']
for e in [
    mne,
    mne_connectivity,
    rich,
    antio,
    plotly,
    sklearn,
    textual,
    loguru,
    pandas,
    fastapi,
    nicegui,
    psychopy,
    werkzeug,
    starlette,
    omegaconf,
    sqlalchemy,
    latex2mathml
]:
    if e.__name__ == 'sklearn':
        lst.append(f'scikit-learn=={e.__version__}')
        continue
    try:
        lst.append(f'{e.__name__}=={importlib.metadata.version(e.__name__)}')
    except:
        lst.append(f'{e.__name__}')

[print(e) for e in lst]

with open('./requirements.txt', 'w') as f:
    f.writelines([e+'\n' for e in lst])
