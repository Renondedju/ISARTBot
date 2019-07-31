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

from discord.ext import commands

class TestCommands(commands.Cog):

    @commands.group(pass_context=True, invoke_without_command=True, hidden=True)
    async def test(self, ctx):
        """ Creates a command group"""

        if ctx.invoked_subcommand is None:
            await ctx.send("Test v2 !")

    @test.command(pass_context=True, hidden=True)
    async def lang(self, ctx, lang: str, key: str):
        """ Returns the content of a language key """

        if (not (lang in ctx.bot.langs) or not (ctx.bot.langs[lang].has_key(key))):
            await ctx.send("No such lang or key")
        else:
            await ctx.send(ctx.bot.langs[lang].get_key(key))

    @test.command(name='error')
    async def _error(self, ctx):
        raise ValueError("Test of unhandled exception")

def setup(bot):
    bot.add_cog(TestCommands())