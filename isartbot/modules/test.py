# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018 Renondedju

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

import asyncio
import discord

from isartbot.bot_decorators import is_dev, is_admin, dont_run
from discord.ext             import commands
from json                    import dumps

class Test_commands(commands.Cog):

    def __init__(self, bot):

        #Private
        self.__bot = bot

    @commands.group(pass_context=True, invoke_without_command=True, hidden=True)
    @commands.check(is_dev)
    async def test(self, ctx):
        """ Creates a command group """

        if ctx.invoked_subcommand is None:
            await ctx.send("Test !")

    @test.command(name='error')
    async def _error(self, ctx):
        raise ValueError("Test of unhandled exception")

    @_error.error
    async def _error_error(self, ctx, error):
        await ctx.bot.on_error(ctx, error)

    @test.error
    async def test_error(self, ctx, error):

        if isinstance(error, commands.CheckFailure):
            await ctx.send("You need to be a dev to use this command")
            return
        
        await ctx.bot.on_error(ctx, error)

    @test.command(name='admin')
    @commands.check(is_admin)
    async def _admin(self, ctx):
        await ctx.send("You are an admin !")
        return

    @_admin.error
    async def _admin_error(self, ctx):
        await ctx.send("You are not an admin !")
        return

    @test.command(name='dontrun', pass_context=True)
    @commands.check(dont_run)
    async def dontrun(self, ctx):
        await ctx.send('Mhhh, i guess there is a problem')
        return

    @dontrun.error
    async def dontrun_error(self, ctx, error):

        if isinstance(error, commands.CheckFailure):
            await ctx.send("You cannot run this command :)")
            return

        await ctx.bot.on_error(ctx, error)

    ###             Settings group
    @test.group(pass_context=True, invoke_without_command=True)
    async def settings(self, ctx):
        """
            Creates a settings command group
        """
        if ctx.invoked_subcommand is None:
            await ctx.send('nothing to do.')
        return

    @settings.command(name='read')
    async def __settings_read(self, ctx):

        string = dumps(self.__bot.settings.get(), indent=4)

        await ctx.send("```json\n{}\n```".format(string))

        return

    @settings.command(name='write')
    async def __settings_write(self, ctx, data, key, *args):

        if self.__bot.settings.write(data, key, *args):
            await ctx.send("Settings have been modified successfully !")
        else:
            await ctx.send("Sorry but the setting you tried to write has been denied.")

        return

def setup(bot):
    bot.add_cog(Test_commands(bot))