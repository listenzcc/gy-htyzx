from datetime import datetime

# key: tailwind classes
ROLES = {
    'ADMIN': 'bg-red-100 text-red-800',
    'USER': 'bg-blue-100 text-blue-800',
    'GUEST': 'bg-gray-100 text-gray-800'
}

GENDERS = {
    'male': 'text-blue-800',
    'female': 'text-red-800'
}

EDUCATIONS = {
    'middle school': 'bg-yellow-100 text-yellow-800',      # 初中
    'high school': 'bg-green-100 text-green-800',          # 高中
    'associate degree': 'bg-purple-100 text-purple-800',   # 大专
    'bachelor': 'bg-blue-100 text-blue-800',               # 本科
    'master': 'bg-indigo-100 text-indigo-800',             # 硕士
    'doctorate': 'bg-violet-100 text-violet-800'           # 博士
}


# Reuseable styles
class STYLES:
    # Text
    plainText = 'text-gray-800'
    errorText = 'text-red-800'

    # Input
    nonEditable = 'bg-gray-100'

    # Card
    fullCard = 'w-full shadow-lg border'
    columnCard = 'w-1/3 shadow-lg border'
    cardTitleLabel = 'text-lg font-semibold'

    # Page
    pageTitle = 'text-3xl font-bold tracking-tight'
    pageSubTitle = 'text-gray-500 text-sm'
    pageBadgeText = 'text-sm italic'

# Notify kwargs


class NOTIFY_KWARGS:
    # Negative
    negative = {'position': 'center', 'type': 'negative'}

    # Positive
    positive = {'position': 'center', 'type': 'positive'}


# Allowed chars for username & password
ALLOWED_USERNAME = 'abcdefghijklmnopqrstuvwxyz1234567890._-@'
ALLOWED_PASSWORD = 'abcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*-=_+()[]{}<>'

# Format
DATE_FMT = '%Y-%m-%d'
FILE_DATE_FMT = '%Y%m%d_%H%M%S'

# How to generate a new user
NEW_USER_DCT = {
    'birth_date': datetime(1936, 12, 12),
    'training_date': datetime.now(),
    'role': 'USER',
    'gender': 'male',
    'education': 'bachelor',
    'is_active': True,
}
