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
import logging

from discord.ext import commands

#TODO Add checks
class ExtCommands(commands.Cog):

    @commands.group(pass_context=True, hidden=True, invoke_without_command=True)
    #@commands.check(is_dev)
    async def ext(self, ctx):
        
        if ctx.invoked_subcommand is None:
            await ctx.send(await ctx.bot.get_translation(ctx, 'invalid_command_usage'))

    def get_ext_name(self, ext : str) -> str:

        ext = ext.replace('.py', '')
        return "isartbot.ext." + ext

    @ext.command(name="load")
    async def _load(self, ctx, *, ext : str):
        """Loads an extension"""

        ext = self.get_ext_name(ext)
        ctx.bot.logger.info(f"Loading extension named: {ext}")
        
        embed = discord.Embed()

        try:
            ctx.bot.load_extension(ext)

        except Exception as e:
            embed.title       = await ctx.bot.get_translation(ctx, 'failure_title')
            embed.description = await ctx.bot.get_translation(ctx, 'ext_load_failure_desc')
            embed.colour      = discord.Color.red()
            await ctx.bot.on_error(ctx, e)

        else:
            embed.title       = await ctx.bot.get_translation(ctx, 'success_title')
            embed.description = await ctx.bot.get_translation(ctx, 'ext_load_success_desc')
            embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    @ext.command(name="unload")
    async def _unload(self, ctx, *, ext : str):
        """Unloads an extension"""

        ext = self.get_ext_name(ext)
        ctx.bot.logger.info(f"Unloading extension named: {ext}")
        
        embed = discord.Embed()

        try:
            ctx.bot.unload_extension(ext)
            
        except Exception as e:
            embed.title       = await ctx.bot.get_translation(ctx, 'failure_title')
            embed.description = await ctx.bot.get_translation(ctx, 'ext_unload_failure_desc')
            embed.colour      = discord.Color.red()
            await ctx.bot.on_error(ctx, e)

        else:
            embed.title       = await ctx.bot.get_translation(ctx, 'success_title')
            embed.description = await ctx.bot.get_translation(ctx, 'ext_unload_success_desc')
            embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    @ext.command(name='reload')
    async def _reload(self, ctx, *, ext : str):
        """Reloads an extension"""

        ext = self.get_ext_name(ext)
        ctx.bot.logger.info(f"Reloading extension named: {ext}")

        embed = discord.Embed()        

        try:
            ctx.bot.unload_extension(ext)
            ctx.bot.load_extension(ext)
            
        except Exception as e:
            embed.title       = await ctx.bot.get_translation(ctx, 'failure_title')
            embed.description = await ctx.bot.get_translation(ctx, 'ext_reload_failure_desc')
            embed.colour      = discord.Color.red()
            await ctx.bot.on_error(ctx, e)

        else:
            embed.title       = await ctx.bot.get_translation(ctx, 'success_title')
            embed.description = await ctx.bot.get_translation(ctx, 'ext_reload_success_desc')
            embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(ExtCommands())