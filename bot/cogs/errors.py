# -*- coding: utf-8 -*-

import logging

from discord.ext import commands

from bot import Cog


log = logging.getLogger(__name__)


IGNORED = (
    commands.CommandNotFound,
    commands.CheckFailure,
)


class Errors(Cog):
    @Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, IGNORED):
            return

        if isinstance(error, commands.UserInputError):
            msg = f'{ctx.author.mention} Bad argument! {error}'
        elif isinstance(error, commands.MissingRequiredArgument):
            msg = f'{ctx.author.mention} Missing argument! {error}.'
        else:
            msg = f'{ctx.author.mention} Something unexpect went wrong! Please try again later.'

            if isinstance(error, commands.CommandInvokeError):
                error = error.original

            log.exception(
                f'Unexpected error in {ctx.command.name} command by {ctx.author} {ctx.author.id}!', exc_info=error
            )

        await ctx.send(msg)


def setup(bot):
    bot.add_cog(Errors(bot))
