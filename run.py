# -*- coding: utf-8 -*-

from bot import Bot
from common import setup_logging


with setup_logging():
    Bot.with_config().run()
