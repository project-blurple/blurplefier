# -*- coding: utf-8 -*-

import asyncio

from discord.ext import commands


class LinkConverter(commands.Converter):
    async def convert(self, ctx, argument):
        if not argument.startswith(('http://', 'https://')):
            raise commands.BadArgument('Not a valid URL!')

        for _ in range(10):
            if ctx.message.embeds and ctx.message.embeds[0].thumbnail:
                return ctx.message.embeds[0].thumbnail.proxy_url

            await asyncio.sleep(1)

        raise commands.BadArgument('Discord proxy image did not load in time.')


class FlagConverter(commands.Converter):
    async def convert(self, ctx, argument):
        if not argument.startswith('--'):
            raise commands.BadArgument('Not a valid flag!')
        return argument


class FlagConverter2(commands.Converter):
    async def convert(self, ctx, argument):
        if not argument.startswith('++'):
            raise commands.BadArgument('Not a valid flag!')
        return argument
