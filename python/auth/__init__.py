import sys
from loguru import logger

sys.path.append('..')  # noqa
from constants import *

logger.add("log/auth_{time:YYYY-MM-DD}.log",
           encoding=ENCODING, rotation='1 day')
