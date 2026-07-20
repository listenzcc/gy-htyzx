from datetime import datetime

# Encoding
ENCODING = 'utf-8'
ENCODING_CN = 'utf-8-sig'

# ------------------------------------------------------------------------------
# key: tailwind classes
ROLES = {
    '管理员': 'bg-red-100 text-red-800',
    '普通用户': 'bg-blue-100 text-blue-800',
    '游客': 'bg-gray-100 text-gray-800'
}

GENDERS = {
    '男': 'text-blue-800',
    '女': 'text-red-800'
}

EDUCATIONS = {
    '初中毕业': 'bg-yellow-100 text-yellow-800',      # 初中
    '高中毕业': 'bg-green-100 text-green-800',          # 高中
    '大专毕业': 'bg-purple-100 text-purple-800',   # 大专
    '本科毕业': 'bg-blue-100 text-blue-800',               # 本科
    '硕士毕业': 'bg-indigo-100 text-indigo-800',             # 硕士
    '博士毕业': 'bg-violet-100 text-violet-800'           # 博士
}


# ------------------------------------------------------------------------------
# Reuseable styles
class STYLES:
    # Text
    plainText = 'text-gray-800'
    errorText = 'text-red-800'
    attentionText = 'text-red-600'
    infoText = 'text-blue-800'

    # Input
    nonEditable = 'bg-gray-100'

    # Card
    fullCard = 'w-full shadow-lg border'
    column3Card = 'w-1/3 shadow-lg border'
    column3_2Card = 'w-2/3 shadow-lg border'
    column4Card = 'w-1/4 shadow-lg border'
    cardTitleLabel = 'text-lg font-semibold'
    cardSubTitleLabel = 'text-md font-semibold'

    # Page
    pageTitle = 'text-3xl font-bold tracking-tight'
    pageSubTitle = 'text-gray-500 text-sm'
    pageBadgeText = 'text-sm italic'

    # Pandas table
    pandasTable = 'w-full max-h-[28em]'


# ------------------------------------------------------------------------------
# Notify kwargs
class NOTIFY_KWARGS:
    # Negative
    negative = {'position': 'center', 'type': 'negative'}

    # Positive
    positive = {'position': 'center', 'type': 'positive'}


# ------------------------------------------------------------------------------
# Date Format
DATE_FMT = '%Y-%m-%d'
FILE_DATE_FMT = '%Y%m%d_%H%M%S'

# ------------------------------------------------------------------------------
# How to generate a new user
NEW_USER_DCT = {
    'birth_date': datetime(1936, 12, 12),
    'training_date': datetime.now(),
    'role': '普通用户',
    'gender': '男',
    'education': '本科毕业',
    'is_active': True,
}

# ------------------------------------------------------------------------------
# Rules for username and password

# Allowed chars for username & password
ALLOWED_USERNAME = 'abcdefghijklmnopqrstuvwxyz1234567890._-@'
ALLOWED_PASSWORD = 'abcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*-=_+()[]{}<>'
DENIED_PASSWORD = ' '

# Basic validation for username and password
USERNAME_VALIDATION = {
    '用户名过短': lambda value: len(value) > 3,
    # all([e in ALLOWED_USERNAME for e in value])
    '用户名包含不支持的字符': lambda value: all([e not in value for e in DENIED_PASSWORD])
}

PASSWORD_VALIDATION = {
    '密码过短': lambda value: len(value) > 5,
    '密码包含不支持的字符': lambda value: all([e in ALLOWED_PASSWORD for e in value])
}
