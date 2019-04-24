# -*- coding: utf-8 -*-

import json

import aioredis
from discord.ext import commands


class Bot(commands.Bot):
    def __init__(self, config, **kwargs):
        super().__init__(
            command_prefix=config['prefix'],
            owner_id=config.get('owner_id'),
            **kwargs,
        )

        self.config = config

        self.redis = None

        extensions = ('jishaku', 'bot.cogs.blurple', 'bot.cogs.errors')

        for name in extensions:
            self.load_extension(name)

    @classmethod
    def with_config(cls, path='config.json'):
        """Create a bot instance with a Config."""

        with open(path) as f:
            data = json.load(f)

        return cls(data)

    async def start(self, *args, **kwargs):
        self.redis = await aioredis.create_redis_pool(self.config['redis'])

        await super().start(*args, **kwargs)

    def run(self):
        super().run(self.config['token'])
