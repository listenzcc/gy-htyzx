"""
File: remove-users.py
Author: Chuncheng Zhang
Date: 2026-07-09
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Remove users.

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


# %% ---- 2026-07-09 ------------------------
# Play ground
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'Remove users from local user db.')
    # parser.add_argument(
    #     '-f', '--file', help='Users file (.csv)', required=True)
    args = parser.parse_args()
    print(args)

    usernames = [
        'admin-1',
        'admin-2',
        'admin-3',
        'admin-4',
        'admin-5',
        'admin-10',
        'admin-11',
    ]

    for name in usernames:
        user_service.remove_user(name)


# %% ---- 2026-07-09 ------------------------
# Pending


# %% ---- 2026-07-09 ------------------------
# Pending
