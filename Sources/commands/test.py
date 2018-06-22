# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2018 Renondedju

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
sys.path.append("./Lib/discord.py")
sys.path.append("../")

from bot_decorators import is_dev
import logs
import discord
import asyncio
import settings
from discord.ext import commands

class Test_commands():

    def __init__(self, bot):

        #Private
        self.__bot = bot

    @commands.group(pass_context=True)
    async def test(self, ctx):
        """
            Creates a command group
        """

        if ctx.invoked_subcommand is None:
            await ctx.send("{0.subcommand_passed} doesn't exists".format(ctx))

    @test.command(name='dev')
    @commands.check(is_dev)
    async def _dev(self, ctx):
        await ctx.send("You are a dev !")
        return

    @_dev.error
    async def _dev_error(self, ctx, error):
        await ctx.send("You are not a dev !")
        return

def setup(bot):
    bot.add_cog(Test_commands(bot))