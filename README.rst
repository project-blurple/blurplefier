=========
Blurplefy
=========

Bot which converts images to different blurple shades or other colors.

-------
Running
-------

The bot can either be run with docker-compose or using another process manager, the steps are explained below:

First you have to create a config file with credentials, you can simply copy the ``example-config.json`` and
edit it with your own values, then save it as ``config.json``.

To run the bot with docker see these steps:

.. code-block :: bash

    docker build -t blurplefy .

    # You can adjust how many workers you want to run here
    docker-compose up --scale workers=2


To run the bot without docker you will need to install and run `Redis <https://redis.io>`_ (see
`here <https://redislabs.com/blog/redis-on-windows-10/>`_ for Windows 10 instructions) as well as
install all the Python requirements using ``pip install -Ur requirements.txt``.

Running the bot and worker can then be done from the root directory of this repository:

.. code-block :: bash

    python -m bot

    python -m worker

And that's it! Have fun with the bot.