# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018-2019 Renondedju

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

from discord.ext     import commands
from isartbot.checks import super_admin, developper, is_developper

class TestCommands(commands.Cog):

    @commands.group(pass_context=True, invoke_without_command=True, hidden=True)
    @commands.check(is_developper)
    async def test(self, ctx):
        """ Creates a command group"""

        if ctx.invoked_subcommand is None:
            await ctx.send(await ctx.bot.get_translation(ctx, 'test'))

    @test.command()
    async def lang(self, ctx, lang: str, key: str):
        """ Returns the content of a language key """

        if (not (lang in ctx.bot.langs) or not (ctx.bot.langs[lang].has_key(key))):
            await ctx.send("No such lang or key")
        else:
            await ctx.send(ctx.bot.langs[lang].get_key(key))

    @test.command()
    async def error(self, ctx):
        raise ValueError("Test of unhandled exception")

    @test.command()
    async def delay(self, ctx):
        await asyncio.sleep(2)
        await ctx.send(await ctx.bot.get_translation(ctx, 'test_wait'))

    @test.command()
    async def groups(self, ctx, user: discord.Member = None):
        
        if user is None : user = ctx.author

        groups = []
        if super_admin(ctx, user) : groups.append("Super admin") 
        if developper (ctx, user) : groups.append("Developper" )

        if len(groups) == 0:
            await ctx.send(f"{user.mention} {await ctx.bot.get_translation(ctx, 'user_has_no_groups')}")
        else:
            await ctx.send(f"{user.mention} {await ctx.bot.get_translation(ctx, 'user_has_groups')}: {groups}")

def setup(bot):
    bot.add_cog(TestCommands())