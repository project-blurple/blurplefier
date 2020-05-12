# -*- coding: utf-8 -*-

import asyncio
import json
import logging
import typing

import discord
from discord.ext import commands

from .converter import FlagConverter, FlagConverter2, LinkConverter
from bot import Cog


log = logging.getLogger(__name__)




def _make_check_command(name, **kwargs):
    @commands.command(name, help=f'{name.title()} an image to get the Blurple User role.', **kwargs)
    async def command(self, ctx, *, who: typing.Union[discord.Member, discord.PartialEmoji, LinkConverter] = None):

        variation = None

        if ctx.message.attachments:
            url = ctx.message.attachments[0].proxy_url
        elif who is None:
            url = ctx.author.avatar_url
            variation = 'avatar'
        else:
            if isinstance(who, str):  # LinkConverter
                url = who
            elif isinstance(who, discord.PartialEmoji):
                url = who.url
            else:
                url = who.avatar_url

        modifier = 'light'

        if modifier is None:
            return

        data = {'modifier': modifier, 'method': name, 'variation': variation, 'url': str(url),
                'guild': ctx.guild.id, 'channel': ctx.channel.id, 'requester': ctx.author.id, 'author': str(ctx.author),
                'message': ctx.message.id}

        # Signal that the request has been queued
        await ctx.message.add_reaction(self.bot.config['queue_emoji'])

        await ctx.bot.redis.rpush('blurple:queue', json.dumps(data))

    return command


def _make_color_command(name, modifier, **kwargs):
    @commands.command(name, help=f'{name.title()} an image.', **kwargs)
    async def command(self, ctx, method: typing.Optional[FlagConverter] = None,
                      variations: commands.Greedy[FlagConverter2] = [None], *,
                      who: typing.Union[discord.Member, discord.PartialEmoji, LinkConverter] = None):

        if method is None:
            method = await self.get_default_blurplefier(ctx)

            if method is None:
                return
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

        data = {'modifier': modifier, 'method': method, 'variation': variations, 'url': str(url),
                'guild': ctx.guild.id, 'channel': ctx.channel.id, 'requester': ctx.author.id, 'author': str(ctx.author),
                'message': ctx.message.id}

        # Signal that the request has been queued
        await ctx.message.add_reaction(self.bot.config['queue_emoji'])

        await ctx.bot.redis.rpush('blurple:queue', json.dumps(data))

    return command


class Blurplefy(Cog):
    def __init__(self, bot):
        super().__init__(bot)

        # Reaction user cache for fewer lookups
        self._ready = asyncio.Event()

        self._reaction_users = {
            '1\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}': set(),
            '2\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}': set(),
        }

    
    
    blurplefy = _make_color_command('blurplefy', 'light', aliases=['blurpefy', 'blurplefly', 'blurplfy', 'blurpify', 'burplfy', 'burplefy', 'burplefly'])
    check = _make_check_command('check')

    @Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(self.bot.config['blurplefier_reaction_channel'])
        message = await channel.fetch_message(self.bot.config['blurplefier_reaction_message'])

        self._ready.clear()
        self._reaction_users = {
            key: set() for key in self._reaction_users.keys()
        }

        for reaction in filter(lambda x: x.emoji in self._reaction_users.keys(), message.reactions):
            async for user in reaction.users(limit=None):
                self._reaction_users[reaction.emoji].add(user.id)

        self._ready.set()
        log.info('Cached all reaction users to blurplefier message.')

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        self._handle_reaction(payload, 'add')

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        self._handle_reaction(payload, 'remove')

    def _handle_reaction(self, payload, action):
        if payload.message_id != self.bot.config['blurplefier_reaction_message']:
            return

        cached = self._reaction_users.get(payload.emoji.name)

        if cached is None:
            return

        # cached.add() / cached.remove()
        getattr(cached, action)(payload.user_id)

    async def get_default_blurplefier(self, ctx):
        await self._ready.wait()

        user_id = ctx.author.id

        blurplefiers = {
            '1\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}': '--blurplefy',
            '2\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}': '--filter',
        }

        for name, value in blurplefiers.items():
            if user_id in self._reaction_users[name]:
                return value
            
        return 'default--blurplefy'
        