import loguru
import pandas
import fastapi
import nicegui
import psychopy
import werkzeug
import starlette
import omegaconf
import sqlalchemy
import latex2mathml


lst = ['# python==3.11.15']
for e in [
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
    try:
        lst.append(f'{e.__name__}=={e.__version__}')
    except:
        lst.append(f'{e.__name__}')

[print(e) for e in lst]

with open('./requirements.txt', 'w') as f:
    f.writelines([e+'\n' for e in lst])
