Blurplefy
=========

Bot which converts images to different blurple shades or other colors.

-------
Running
-------

The bot can either be run with docker-compose or using another process manager, the steps are explained below:

First you have to create a config file with credentials, you can simply copy the ``example-config.yaml`` and
edit it with your own values, then save it as ``config.yaml``.

Afterwards you'll want to adjust the ``WORKER_COUNT`` environment variable, if using docker you can copy the
``example.env`` file, edit it and save it as ``.env``.

To run the bot with docker see these steps:

```bash
docker-compose up --scale workers=2
```

To run the bot without docker you will need to install and run [Redis](https://redis.io) (see
[here](https://redislabs.com/blog/redis-on-windows-10/) for Windows 10 instructions) as well as
install all the Python requirements using ``pip install -Ur requirements.txt``.

Running the bot and worker can then be done from the root directory of this repository:

```
python -m bot

python -m worker
```
And that's it! Have fun with the bot.
