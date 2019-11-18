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
import logging


from discord.ext     import commands
from isartbot.helper import Helper
from isartbot.checks import is_super_admin, is_developper

class ExtExt(commands.Cog):

    @commands.group(pass_context=True, hidden=True, invoke_without_command=True,
        help="ext_help", description="ext_description")
    @commands.check(is_super_admin)
    async def ext(self, ctx):
        await ctx.send_help(ctx.command)

    def get_ext_name(self, ext : str) -> str:

        ext = ext.replace('.py', '')
        return "isartbot.ext." + ext

    @ext.command(name="load", help="ext_load_help", description="ext_load_description")
    async def _load(self, ctx, *, ext : str):
        """Loads an extension"""

        ext = self.get_ext_name(ext)
        ctx.bot.logger.info(f"Loading extension named: {ext}")
        
        try:
            ctx.bot.load_extension(ext)

        except Exception as e:
            await Helper.send_error(ctx, ctx.channel, "ext_load_failure_desc")
            await ctx.bot.on_error (ctx, e)

        else:
            await Helper.send_success(ctx, ctx.channel, "ext_load_success_desc")

    @ext.command(name="unload", help="ext_unload_help", description="ext_unload_description")
    async def _unload(self, ctx, *, ext : str):
        """Unloads an extension"""

        ext = self.get_ext_name(ext)
        ctx.bot.logger.info(f"Unloading extension named: {ext}")
        
        try:
            ctx.bot.unload_extension(ext)
            
        except Exception as e:
            await Helper.send_error(ctx, ctx.channel, "ext_unload_failure_desc")
            await ctx.bot.on_error(ctx, e)

        else:
            await Helper.send_success(ctx, ctx.channel, "ext_unload_success_desc")

    @ext.command(name='reload', help="ext_reload_help", description="ext_reload_description")
    async def _reload(self, ctx, *, ext : str):
        """Reloads an extension"""

        ext = self.get_ext_name(ext)
        ctx.bot.logger.info(f"Reloading extension named: {ext}")

        try:
            ctx.bot.reload_extension(ext)
            
        except Exception as e:
            await Helper.send_error(ctx, ctx.channel, "ext_reload_failure_desc")
            await ctx.bot.on_error(ctx, e)

        else:
            await Helper.send_success(ctx, ctx.channel, "ext_reload_success_desc")

def setup(bot):
    bot.add_cog(ExtExt())
