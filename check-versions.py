import fastapi
import loguru
import nicegui
import omegaconf
import pandas
import sqlalchemy
import starlette
import werkzeug
import latex2mathml


lst = ['# python==3.11.15']
for e in [
    fastapi,
    loguru,
    nicegui,
    omegaconf,
    pandas,
    sqlalchemy,
    starlette,
    werkzeug,
    latex2mathml
]:
    lst.append(f'{e.__name__}=={e.__version__}')

[print(e) for e in lst]

with open('./requirements.txt', 'w') as f:
    f.writelines([e+'\n' for e in lst])
