# -*- coding: utf-8 -*-

import aioredis
from discord.ext import commands

import ruamel.yaml


async def is_blacklisted(ctx):
    role_id = ctx.bot.config['blacklist_role']
    return not any(r.id == role_id for r in ctx.author.roles)


class Bot(commands.Bot):

    def __init__(self, config, **kwargs):
        super().__init__(
            command_prefix=config['bot']['prefix'],
            owner_id=config['bot'].get('owner_id'),
            **kwargs,
        )

        self.config = config

        self.redis = None

        extensions = ('jishaku', 'bot.cogs.blurple', 'bot.cogs.errors', 'bot.cogs.help')

        for name in extensions:
            self.load_extension(name)

        self.add_check(is_blacklisted)

    @classmethod
    def with_config(cls, path='config.yaml'):
        """Create a bot instance with a Config."""

        with open(path, encoding='utf-8') as f:
            data = ruamel.yaml.safe_load(f)

        return cls(data)

    async def start(self, *args, **kwargs):
        self.redis = await aioredis.create_redis_pool(**self.config['redis'])

        await super().start(*args, **kwargs)

    def run(self):
        super().run(self.config['bot']['token'])
