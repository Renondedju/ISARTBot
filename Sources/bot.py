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

#Importing discord libraries (local)
import sys
sys.path.insert(0, "./Lib/discord.py")

import logs
import discord
import asyncio
import settings
import traceback
import bot_decorators
from discord.ext import commands

class Bot(discord.ext.commands.Bot):
    """ Main bot class """

    def __init__(self, *args, **kwargs):
        """ Inits and runs the bot """

        super().__init__(command_prefix = "!", *args, **kwargs)

        #Private
        self.__settings     = settings.Settings()
        self.__commands     = self.__settings.get("bot", "commands")
        self.__logs         = logs.Logs(enabled = self.__settings.get("logs"))
        self.command_prefix = self.__settings.get("bot", "prefix")

        self.loop.create_task(self.load_cog())

        self.add_check(self.globally_block_dms)
        self.add_check(self.check_enable)
        self.add_check(self.log_command)

        self.run(self.__settings.get("bot", "token"))

        self.__logs.close()

    async def load_cog(self):
        """ Loads all the cogs of the bot defined into the settings.json file """

        for name, enabled in self.__commands.items():
            if (name != ""):
                name = name.strip('_')

                try:
                    self.load_extension  ('commands.' + name)
                    self.__logs.print    ('Loaded the command {0}, enabled = {1}'
                        .format(name, str(enabled.get('enabled'))))

                except Exception as e:
                    await self.on_error(None, e)
                    self.__logs.print('Failed to load extension named command.{0}'.format(name))

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

        self.__logs.print('------------')
        self.__logs.print('Logged in as')
        self.__logs.print('Username : {0}#{1}'.format(self.user.name, self.user.discriminator))
        self.__logs.print('User ID  : {0}'    .format(self.user.id))
        self.__logs.print('------------')

    async def on_error(self, ctx, error):
        """ Sends errors reports if needed """

        ignored = (commands.CommandNotFound, commands.UserInputError)
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
        self.__logs.print('Ignoring exception in command {}:'.format(ctx.command))
        for err in traceback.format_exception(type(error), error, error.__traceback__):
            if (err[len(err) - 1] == '\n'):
                err = err[:-1]
            self.__logs.print(err)

        try:
            errors = traceback.format_tb(error.__traceback__)
            embed  = discord.Embed(description =
                "Oops an unexpected error occured !" +
                "\nPlease [open an issue](https://github.com/BasileCombet/ISARTBot/issues)" +
                " on github if this error is recurrent\n" +
                "Make sure to include a screenshot of this message\n```\n" +
                errors[len(errors) - 1] + 
                "\n```",
                title = "Error")

            embed.set_footer(text=self.__logs.get_time)
            embed.colour = discord.Colour.red()

            await ctx.send(embed = embed)
        except:
            return

        return

    async def on_command_error(self, ctx, error):
        """ Handles unhandeled errors """

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return
        
        await self.on_error(ctx, error)

    ###Checks
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

        if bot_decorators.is_dev(ctx):
            return True
        
        enabled = ctx.bot.settings.get("enabled", command=ctx.command.name)

        if (enabled is False):
            await ctx.send("Sorry, but this command is disabled for now !")

        return enabled

    async def log_command(self, ctx):
        """ Logs every command """
        author  = '{0}#{1}'     .format(ctx.author.name, ctx.author.discriminator)
        channel = '{1.name}/{0}'.format(ctx.channel.name, ctx.channel.category)

        self.__logs.print('{0}\t{1} : {2}'.format(author, channel, ctx.message.content))

        return True