# -*- coding: utf-8 -*-

from . import Worker
from common import setup_logging


with setup_logging():
    Worker.with_config().run()
