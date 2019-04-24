# -*- coding: utf-8 -*-

from discord.ext import commands


class Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def redis(self):
        return self.bot.redis
