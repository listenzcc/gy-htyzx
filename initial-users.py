"""
File: initial-users.py
Author: Chuncheng Zhang
Date: 2026-06-21
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Initialize users for development.

Functions:
    1. Requirements and constants
    2. Function and class
    3. Play ground
    4. Pending
    5. Pending
"""


# %% ---- 2026-06-21 ------------------------
# Requirements and constants
import os
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from python.auth.user_service import UserService
from python.auth.database import DatabaseManager


# %%
GENDERS = ['male', 'female']
BIRTH_DATE_RANGE = [datetime(1980, 1, 1), datetime(2001, 1, 1)]
TRAINING_DATE_RANGE = [datetime(2020, 1, 1), datetime(2026, 1, 1)]
EDUCATIONS = [
    'middle school',      # 初中
    'high school',        # 高中
    'associate degree',   # 大专
    'bachelor',           # 本科
    'master',             # 硕士
    'doctorate'           # 博士
]
NUM_ADMIN = 3
NUM_USER = 100
NUM_GUEST = 10

# %% ---- 2026-06-21 ------------------------
# Function and class


def random_date(start, end):
    """返回 start 和 end 之间的随机日期（包含两端）"""
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


# 示例：2024-01-01 到 2024-12-31 之间
start = datetime(2024, 1, 1)
end = datetime(2024, 12, 31)


def generate_user_randomly(username: str = None, password: str = None, role: str = 'USER'):
    if username is None:
        username = f'{role.lower()}{random.randint(1, 1000)}'

    if password is None:
        password = role.lower()

    dct = {
        'username': username,
        'password': password,
        'role': role
    }

    dct.update({
        'gender': random.choice(GENDERS),
        'education': random.choice(EDUCATIONS),
        'birth_date': random_date(*BIRTH_DATE_RANGE).date(),
        'training_date': random_date(*TRAINING_DATE_RANGE).date()
    })

    return dct


# %% ---- 2026-06-21 ------------------------
# Play ground
db_file = Path('./db/auth.db')
session_folder = Path('./.nicegui')

# ! Remove existing db
os.rename(db_file, db_file.with_suffix(f'.{time.time()}.db.bak'))

# Auth db
# 1. 初始化数据库
db_manager = DatabaseManager('sqlite:///db/auth.db', echo=False)
db_manager.create_tables()
db_manager.initialize_data()

# 2. 创建服务实例
session = db_manager.get_session()
user_service = UserService(session)

roles = ['ADMIN'] * NUM_ADMIN + ['USER'] * NUM_USER + ['GUEST'] * NUM_GUEST
for role in roles:
    user_dct = generate_user_randomly(role=role)
    try:
        user_service.create_user(**user_dct)
    except:
        pass

# %% ---- 2026-06-21 ------------------------
# Pending


# %% ---- 2026-06-21 ------------------------
# Pending
