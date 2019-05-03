# -*- coding: utf-8 -*-

import json
import typing

import discord
from discord.ext import commands

from .converter import FlagConverter, FlagConverter2, LinkConverter
from bot import Cog


def _make_color_command(name, modifier, **kwargs):
    @commands.command(name, help=f'{name.title()} an image.', **kwargs)
    async def command(self, ctx, method: typing.Optional[FlagConverter] = None, variations: commands.Greedy[FlagConverter2] = [None], *,  who: typing.Union[discord.Member, discord.PartialEmoji, LinkConverter] = None):

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

        if modifier is 'blurplefy':
            if ctx.guild.get_role(self.bot.config['blurple_light_id']) in ctx.author.roles:
                final_modifier = 'light'
            elif ctx.guild.get_role(self.bot.config['blurple_dark_id']) in ctx.author.roles:
                final_modifier = 'dark'
            else:
                await ctx.channel.send('You need to be a part of a team first.')
                return
        else:
            final_modifier = modifier

        data = {'modifier': final_modifier, 'method': method, 'variation': variations, 'url': str(url), 'channel': ctx.channel.id, 'requester': ctx.author.id, 'message': ctx.message.id}

        # Signal that the request has been queued
        await ctx.message.add_reaction(self.bot.config['queue_emoji'])

        await ctx.bot.redis.rpush('blurple:queue', json.dumps(data))



    return command


class Blurplefy(Cog):
    lightfy = _make_color_command('lightfy', 'light')
    darkfy = _make_color_command('darkfy', 'dark')
    blurplefy = _make_color_command('blurplefy', 'blurplefy')
