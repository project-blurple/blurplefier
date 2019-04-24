# -*- coding: utf-8 -*-

from discord.ext import commands

from bot import Cog


IGNORED = (
    commands.CommandNotFound,
    commands.CheckFailure,
)


class Errors(Cog):
    @Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, IGNORED):
            return

        # TODO: Proper error handler
        await ctx.send(str(error))


def setup(bot):
    bot.add_cog(Errors(bot))
