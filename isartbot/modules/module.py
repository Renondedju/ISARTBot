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

from isartbot.bot_decorators import is_dev
from discord.ext             import commands

class Module_commands(commands.Cog):

    def __init__(self, bot):

        #Private
        self.bot = bot

    def get_module_name(self, module : str) -> str:

        module = module.replace('.py', '').replace('commands.', '')
        return "isartbot.modules." + module

    @commands.group(pass_context=True, hidden=True, invoke_without_command=True)
    @commands.check(is_dev)
    async def module(self, ctx):
        
        if ctx.invoked_subcommand is None:
            await ctx.send("{0.subcommand_passed} doesn't exists".format(ctx))

    @module.error
    async def module_error(self, ctx, error):

        if isinstance(error, commands.CheckFailure):
            await ctx.send("You need to be a dev to use this command")
        else:
            await ctx.bot.on_error(ctx, error)            

    @module.command(name="load")
    async def _load(self, ctx, *, module : str):
        """Loads a module."""

        module = self.get_module_name(module)

        try:
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.bot.send_fail(ctx,
                "Failed to load extension"
                "\n{}: {}".format(type(e).__name__, e),
                "Extension")
        else:
            await ctx.bot.send_success(ctx,
                "Successfully loaded extension named {}".format(module),
                "Extension")

    @module.command(name="unload")
    async def _unload(self, ctx, *, module : str):
        """Unloads a module."""

        module = self.get_module_name(module)

        try:
            self.bot.unload_extension(module)
        except Exception as e:
            await ctx.bot.send_fail(ctx, "Failed to unload extension"
                "\n{}: {}".format(type(e).__name__, e), "Extension")
        else:
            await ctx.bot.send_success(ctx,
            "Successfully unloaded extension named {}".format(module),
            "Extension")

    @module.command(name='reload')
    async def _reload(self, ctx, *, module : str):
        """Reloads a module."""

        module = self.get_module_name(module)

        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.bot.send_fail(ctx,
                "Failed to reload extension"
                "\n{}: {}".format(type(e).__name__, e),
                "Extension")
        else:
            await ctx.bot.send_success(ctx,
            "Successfully reloaded extension named {}".format(module),
            "Extension")

    @module.command(name='enable')
    async def _enable(self, ctx, module : str):

        if ctx.bot.settings.get(command = module) is None:
            await ctx.bot.send_fail(ctx,
                f"Module named isartbot.commands.{module} does not exists",
                "Module")
            return

        ctx.bot.settings.write(True, 'enabled', command = module)
        self.bot.logs.print("Enabled the module named '{}'".format(module))
        await ctx.bot.send_success(ctx,
            f"Module named isartbot.commands.{module} has successfully been enabled",
            "Module")

    @module.command(name='disable')
    async def _disable(self, ctx, module : str):
        
        if ctx.bot.settings.get(command = module) is None:
            await ctx.bot.send_fail(ctx,
                f"Module named isartbot.commands.{module} does not exists",
                "Module")
            return

        ctx.bot.settings.write(False, 'enabled', command = module)
        self.bot.logs.print("Disabled the module named '{}'".format(module))
        await ctx.bot.send_success(ctx,
            f"Module named isartbot.commands.{module} has successfully been disabled",
            "Module")

    @_enable.error
    @_disable.error
    async def _error(self, ctx, error):

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.bot.send_fail(ctx, str(error), "Module")
            return

        await ctx.bot.on_error(ctx, error)  

def setup(bot):
    bot.add_cog(Module_commands(bot))