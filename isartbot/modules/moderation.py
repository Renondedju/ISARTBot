# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018 - 2019 Renondedju, Torayl

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import discord
import asyncio

from discord.ext                   import commands
from isartbot.bot_decorators       import is_moderator, is_dev

class ModerationCommands(commands.Cog, name='mod'):
    """Helps with moderation"""

    def __init__(self, bot):

        #Private
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True, hidden=True)
    @commands.check(is_dev)
    async def mod(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.bot.send_fail(ctx,
                "Moderation subcommand not recognized.\n"
                .format(self.bot.settings.get("bot", "prefix")),
                "Moderation")

    #Prune command
    @mod.command(name='prune', pass_context=True, hidden=True)
    @commands.check(is_moderator)
    async def _prune(self, ctx, number : int, member : discord.Member = None):
        """Deletes a certain amount of the latest messages in this text channel"""
        messages = []
        if (member is None):
            messages = await ctx.channel.history(limit=number + 1).flatten()
        else:
            async for message in ctx.channel.history(limit=number + 1):
                if (message.author == member):
                     messages.append(message)
            messages.append(ctx.message)

        await ctx.channel.delete_messages(set(messages))
        return

def setup(bot):
    bot.add_cog(ModerationCommands(bot))
