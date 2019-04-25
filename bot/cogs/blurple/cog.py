# -*- coding: utf-8 -*-

import json
import typing

import discord
from discord.ext import commands

from .converter import LinkConverter
from bot import Cog


def _make_color_command(name, modifier, **kwargs):
    @commands.command(name, help=f'{name.title()} an image.', **kwargs)
    async def command(self, ctx, *, who: typing.Union[discord.Member, discord.PartialEmoji, LinkConverter] = None):

        if ctx.message.attachments:
            url = ctx.message.attachments[0].proxy_url
        elif who is None:
            url = ctx.author.avatar_url
        else:
            if isinstance(who, str):  # LinkConverter
                url = who
            elif isinstance(who, discord.PartialEmoji):
                url = who.url
            else:
                url = who.avatar_url

        data = {'modifier': modifier, 'url': str(url), 'channel': ctx.channel.id, 'requester': ctx.author.id, 'message': ctx.message.id}

        await ctx.bot.redis.rpush('blurple:queue', json.dumps(data))

        # Signal that the request has been queued
        await ctx.message.add_reaction(self.bot.config['queue_emoji'])

    return command


class Blurplefy(Cog):
    lightfy = _make_color_command('lightfy', 'light')
    darkfy = _make_color_command('darkfy', 'dark')
