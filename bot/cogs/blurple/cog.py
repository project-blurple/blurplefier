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


async def get_modifier(self, ctx):
    guild = self.bot.get_guild(self.bot.config['project_blurple_guild'])
    if guild.get_role(self.bot.config['blurple_light_role']) in ctx.author.roles or guild.get_role(
            self.bot.config['pending_blurple_light_role']) in ctx.author.roles:
        return 'light'
    elif guild.get_role(self.bot.config['blurple_dark_role']) in ctx.author.roles or guild.get_role(
            self.bot.config['pending_blurple_dark_role']) in ctx.author.roles:
        return 'dark'
    else:
        await ctx.channel.send(f'<@!{ctx.author.id}> You need to be a part of a team first. To join a team, use the `+rollteam` command on the Blurplefied bot.')
        return None


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

        modifier = await get_modifier(self, ctx)
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

        if modifier == 'blurplefy':
            final_modifier = await get_modifier(self, ctx)
            if final_modifier is None:
                return
        else:
            final_modifier = modifier

        data = {'modifier': final_modifier, 'method': method, 'variation': variations, 'url': str(url),
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
            '1\N{COMBINING ENCLOSING KEYCAP}': set(),
            '2\N{COMBINING ENCLOSING KEYCAP}': set(),
        }

    lightfy = _make_color_command('lightfy', 'light')
    darkfy = _make_color_command('darkfy', 'dark')
    blurplefy = _make_color_command('blurplefy', 'blurplefy')
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
            '1\N{COMBINING ENCLOSING KEYCAP}': '--blurplefy',
            '2\N{COMBINING ENCLOSING KEYCAP}': '--filter',
        }

        for name, value in blurplefiers.items():
            if user_id in self._reaction_users[name]:
                return value

        guild_id = self.bot.config['project_blurple_guild']
        channel_id = self.bot.config['blurplefier_reaction_channel']
        message_id = self.bot.config['blurplefier_reaction_message']

        message_link = f'https://discordapp.com/channels/{guild_id}/{channel_id}/{message_id}'

        embed = discord.Embed(
            colour=discord.Colour(0x7289da),
            description=f"To choose a default Blurplefier, jump to [*this message*]({message_link})"
        )
        embed.set_footer(text=f"Blurplefier | {str(ctx.author)}", icon_url=self.bot.config['footer_thumbnail_url'])

        await ctx.channel.send(f'<@!{ctx.author.id}> You need to choose a default blurplefier first.', embed=embed)
