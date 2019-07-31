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

import sys
import discord
import asyncio
import logging
import logging.config
import configparser
import traceback

from   discord.ext import commands
from   os.path     import abspath

class Bot(discord.ext.commands.Bot):
    """ Main bot class """

    __slots__ = ("settings", "extensions", "config_file")

    def __init__(self, *args, **kwargs):
        """ Inits and runs the bot """

        super().__init__(command_prefix = "!", *args, **kwargs)

        self.config_file = abspath('./settings.ini')

        # Setting up logging
        logging.config.fileConfig(self.config_file)
        self.logger = logging.getLogger('isartbot')

        # Loading settings
        self.logger.info('Settings file located at {}'.format(self.config_file))
        self.settings = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
        self.settings.read(self.config_file)

        self.extensions        = self.settings['extensions']
        self.command_prefix = self.settings.get('common', 'prefix')

        self.add_check(self.log_command)

        self.loop.create_task(self.load_extensions())

        self.run(self.settings.get('common', 'token'))

    async def load_extensions(self):
        """ Loads all the cogs of the bot defined into the settings.ini file """

        try:
            await self.wait_for("ready", timeout=30)
            self.logger.info("Loading extensions...")
        except asyncio.futures.TimeoutError:
            self.logger.warning("Wait for on_ready event timed out, loading the extensions anyway...")

        for (extension, enabled) in self.settings.items("extensions"):
            if self.extensions.getboolean(extension):
                try:
                    self.load_extension("v2.ext." + extension)
                    self.logger.info   (f"Loaded extension named v2.ext.{extension}")
                except Exception as e:
                    await self.on_error(None, e)
                    self.logger.error(f"Failed to load extension named v2.ext.{name}")
            else:
                self.logger.info(f"Ignored extension named v2.ext.{extension}")

        return

    # --- Events ---

    async def on_ready(self):
        """
            Executed when the bot is connected
            to discord and ready to operate
        """

        self.logger.info("------------")
        self.logger.info("Logged in as")
        self.logger.info("Username : {0}#{1}".format(self.user.name, self.user.discriminator))
        self.logger.info("User ID  : {0}"    .format(self.user.id))
        self.logger.info("------------")

    async def on_command_error(self, ctx, error):
        """ Handles unhandled errors """

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        await self.on_error(ctx, error)

    async def on_error(self, ctx, error):
        """ Sends errors reports if needed """

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, (commands.CommandNotFound, commands.UserInputError, commands.CheckFailure)):
            self.logger.warning(f"Ignored exception : {error}")
            return

        # All other Errors not returned come here... And we can just print the default TraceBack.
        if ctx is not None:
            self.logger.error('Ignoring exception in command {}:'.format(ctx.command))
        else:
            self.logger.error('Ctx is empty, this might be comming from the module loading function:')

        for err in traceback.format_exception(type(error), error, error.__traceback__):
            index = 0
            for i, char in enumerate(err):
                if (char == '\n'):
                    self.logger.error(err[index:i])
                    index = i + 1

        return

    # --- Checks ---

    async def log_command(self, ctx):
        """ Logs every command """

        author  = '{0}#{1}'     .format(ctx.author.name, ctx.author.discriminator)
        channel = '{2.name}/{1.name}/{0}'.format(ctx.channel.name, ctx.channel.category, ctx.guild)

        self.logger.info('{0} -> {1} : {2}'.format(author, channel, ctx.message.content))

        return True
