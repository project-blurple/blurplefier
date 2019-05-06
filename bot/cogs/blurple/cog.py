# -*- coding: utf-8 -*-

import json
import typing

import discord
from discord.ext import commands

from .converter import FlagConverter, FlagConverter2, LinkConverter
from bot import Cog





async def get_modifier(self, ctx):
    guild = self.bot.get_guild(self.bot.config['project_blurple_guild'])
    if guild.get_role(self.bot.config['blurple_light_role']) in ctx.author.roles:
        return 'light'
    elif guild.get_role(self.bot.config['blurple_dark_role']) in ctx.author.roles:
        return 'dark'
    else:
        await ctx.channel.send('You need to be a part of a team first.')
        return None


async def get_default_blurplefier(self, ctx):
    message = await self.bot.get_guild(self.bot.config['project_blurple_guild']).get_channel(
        self.bot.config['blurplefier_reaction_channel']).fetch_message(self.bot.config['blurplefier_reaction_message'])
    reactions = message.reactions

    reaction = next((x for x in reactions if x.emoji == '1⃣'))
    if len((await reaction.users().filter(lambda x: x.id == ctx.author.id).flatten())) != 0:
        return '--blurplefy'

    reaction = next((x for x in reactions if x.emoji == '2⃣'))
    if len((await reaction.users().filter(lambda x: x.id == ctx.author.id).flatten())) != 0:
        return '--filter'

    description = f"To choose a default Blurplefier, jump to [*this message*](https://discordapp.com/channels/{self.bot.config['project_blurple_guild']}/{self.bot.config['blurplefier_reaction_channel']}/{self.bot.config['blurplefier_reaction_message']})"
    embed = discord.Embed(colour=discord.Colour(0x7289da), description=description)
    embed.set_footer(text=f"Blurplefier | {str(ctx.author)}",
                     icon_url=self.bot.config['footer_thumbnail_url'])
    await ctx.channel.send(f'<@!{ctx.author.id}> You need to choose a default blurplefier first.', embed=embed)
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
            method = await get_default_blurplefier(self, ctx)
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
    lightfy = _make_color_command('lightfy', 'light')
    darkfy = _make_color_command('darkfy', 'dark')
    blurplefy = _make_color_command('blurplefy', 'blurplefy')
    check = _make_check_command('check')
