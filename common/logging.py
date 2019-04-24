# -*- coding: utf-8 -*-

"""
Copyright (c) 2017 - 2019 Lilly (SnowyLuma) Berner

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import contextlib
import logging


# Loggers which have static levels regardless of debug or normal mode
LEVEL_OVERWRITES = {
    'discord': logging.INFO,
    'discord.state': logging.WARNING,
    'PIL': logging.INFO,
    'websockets': logging.INFO,
}


@contextlib.contextmanager
def setup_logging(*, process_ids=False):
    """
    Context manager which sets up logging to stdout and shuts down logging on exit.

    Depending on the value of the MOUSEY_DEBUG environment value the log level will be set to INFO or DEBUG.

    Parameters
    ----------
    process_ids : bool
        Controls whether process IDs should be shown in the log. Defaults to False.
    """

    level = logging.INFO  # logging.DEBUG if DEBUG else logging.INFO

    if not process_ids:
        fmt = '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s'
    else:
        fmt = '[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s]: %(message)s'

    try:
        root = logging.getLogger()
        root.setLevel(level)

        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S'))

        root.addHandler(handler)

        for name, value in LEVEL_OVERWRITES.items():
            logging.getLogger(name).setLevel(value)

        _fix_sanic_access()

        yield
    finally:
        logging.shutdown()


def _fix_sanic_access():
    # The sanic access logger uses a different log format which is incompatible with the catch-all used above.
    # By default the access log would show empty messages (only the timestamp), due to this a separate format is used.

    fmt = '[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s]: %(request)s %(status)d %(byte)d %(message)s'

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S'))

    log = logging.getLogger('sanic.access')

    # It's important the access logger does not propagate logs, else the catch-all will still log a duplicate empty line
    log.propagate = False
    log.addHandler(handler)
