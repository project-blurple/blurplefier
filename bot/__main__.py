# -*- coding: utf-8 -*-

from . import Bot
from common import setup_logging


with setup_logging():
    Bot.with_config().run()
