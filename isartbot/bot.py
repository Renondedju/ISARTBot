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

import discord
import asyncio
import traceback

from .logs           import Logs
from .settings       import Settings
from .bot_decorators import is_dev
from  discord.ext    import commands

class Bot(discord.ext.commands.Bot):
    """ Main bot class """

    def __init__(self, *args, **kwargs):
        """ Inits and runs the bot """

        super().__init__(command_prefix = "!", *args, **kwargs)

        #Private
        self.__settings     = Settings()
        self.__commands     = self.__settings.get("bot", "commands")
        self.logs           = Logs(self, enabled = self.__settings.get("logs"))
        self.command_prefix = self.__settings.get("bot", "prefix")

        self.logs.print('Initializing bot ...')

        self.add_check(self.trigger_typing)
        self.add_check(self.globally_block_dms)
        self.add_check(self.log_command)
        self.add_check(self.check_enable)

        self.loop.create_task(self.load_cog())

        self.run(self.__settings.get("bot", "token"))

        self.logs.close()

    async def load_cog(self):
        """ Loads all the cogs of the bot defined into the settings.json file """

        try:
            await self.wait_for('ready', timeout=30)
        except asyncio.futures.TimeoutError:
            self.logs.print("Wait for on_ready event timed out, loading the cogs anyway.")

        for name, enabled in self.__commands.items():
            if (name != ""):
                name = name.strip('_')

                try:
                    text = str(enabled.get('enabled'))
                    self.load_extension('isartbot.modules.' + name)
                    self.logs.print    ('Loaded the module {} : enabled = {}'.format(name, text))

                except Exception as e:
                    await self.on_error(None, e)
                    self.logs.print('Failed to load extension named modules.{0}'.format(name))

        return

    @property
    def settings(self):
        return self.__settings

    async def send_success(self, ctx, message, title=""):
        """ Send a successfull message """

        embed = discord.Embed(
            title       = title,
            description = message,
            colour      = discord.Color.green())

        return await ctx.send(embed=embed)

    async def send_fail(self, ctx, message, title=""):
        """ Send a failed message """

        embed = discord.Embed(
            title       = title,
            description = message,
            colour      = discord.Color.red())

        return await ctx.send(embed=embed)

    #Events
    async def on_ready(self):
        """
            Executed when the bot is connected
            to discord and ready to operate
        """

        self.logs.print('------------')
        self.logs.print('Logged in as')
        self.logs.print('Username : {0}#{1}'.format(self.user.name, self.user.discriminator))
        self.logs.print('User ID  : {0}'    .format(self.user.id))
        self.logs.print('------------')

    async def on_error(self, ctx, error):
        """ Sends errors reports if needed """

        ignored = (commands.CommandNotFound,
                   commands.UserInputError,
                   commands.CheckFailure)
        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)
        
        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send("Hey no DMs!")
            except:
                return
        
        # All other Errors not returned come here... And we can just print the default TraceBack.
        if ctx is not None:
            self.logs.print('Ignoring exception in command {}:'.format(ctx.command))
        else:
            self.logs.print('Ctx is empty, this might be comming from the module loading function:')

        for err in traceback.format_exception(type(error), error, error.__traceback__):
            if (err[len(err) - 1] == '\n'):
                err = err[:-1]
            self.logs.print(err)

        try:
            errors = traceback.format_tb(error.__traceback__)
            embed  = discord.Embed(description =
                "Oops an unexpected error occurred !" +
                "\nPlease [open an issue](https://github.com/BasileCombet/ISARTBot/issues)" +
                " on github if this error is recurrent\n" +
                "Make sure to include a screenshot of this message\n```\n" +
                errors[len(errors) - 1] + 
                "\n```",
                title = "Error")

            embed.set_footer(text=self.logs.get_time)
            embed.colour = discord.Colour.red()

            await ctx.send(embed = embed)
        except:
            return

        return

    async def on_command_error(self, ctx, error):
        """ Handles unhandled errors """

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return
        
        await self.on_error(ctx, error)

    ###Checks
    async def trigger_typing(self, ctx):
        """ Triggers typing """

        await ctx.trigger_typing()

        return True

    async def globally_block_dms(self, ctx):
        """
            Checks if the messages provides from
            a guild or a DM
        """

        result = not (ctx.guild is None)

        if result is False:
            raise commands.NoPrivateMessage()

        return result

    async def check_enable(self, ctx):
        """
            Checks if the command is enabled or not
        """

        if is_dev(ctx):
            return True
        
        command = ctx.command.root_parent
        if (command is None):
            command = ctx.command

        enabled = ctx.bot.settings.get("enabled", command=command.name)

        if (enabled == False):
            await self.send_fail(ctx,
                "Sorry, but this command is disabled for now !",
                'Error')

        return enabled

    async def log_command(self, ctx):
        """ Logs every command """
        author  = '{0}#{1}'     .format(ctx.author.name, ctx.author.discriminator)
        channel = '{1.name}/{0}'.format(ctx.channel.name, ctx.channel.category)

        self.logs.print('{0} {1} : {2}'.format(author, channel, ctx.message.content))

        return True