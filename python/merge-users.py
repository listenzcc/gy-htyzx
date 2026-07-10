"""
File: merge-users.py
Author: Chuncheng Zhang
Date: 2026-07-09
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Merge exported users into local user db.

Functions:
    1. Requirements and constants
    2. Function and class
    3. Play ground
    4. Pending
    5. Pending
"""


# %% ---- 2026-07-09 ------------------------
# Requirements and constants
import argparse
from auth.database import DatabaseManager
from auth.user_service import UserService
import pandas as pd

# %%
# Initialize managers
# 1. 初始化数据库
db_manager = DatabaseManager('sqlite:///db/auth.db', echo=False)

# 2. 创建服务实例
session = db_manager.get_session()
user_service = UserService(session)

# %% ---- 2026-07-09 ------------------------
# Function and class


def read_incoming(file):
    df = pd.read_csv(file)
    return df


# %% ---- 2026-07-09 ------------------------
# Play ground
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'Merge exported users into local user db.')
    parser.add_argument(
        '-f', '--file', help='Users file (.csv)', required=True)
    args = parser.parse_args()
    print(args)

    df = read_incoming(args.file)
    print(df)

    user_service.remove_user('cccc')

    for i, row in df.iterrows():
        username = row['username']
        user = user_service.get_user_by_username(username)
        if user is None:
            print(f'可以合并：{username=}')
        else:
            print(f'发现冲突：（用户名已存在）{username=}')


# %% ---- 2026-07-09 ------------------------
# Pending


# %% ---- 2026-07-09 ------------------------
# Pending
