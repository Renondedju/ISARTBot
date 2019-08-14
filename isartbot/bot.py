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

import sys
import discord
import asyncio
import logging
import traceback
import configparser
import logging.config

from isartbot.exceptions import UnauthorizedCommand
from isartbot.help       import HelpCommand
from isartbot.lang       import Lang
from isartbot.models     import ServerPreferences
from isartbot.checks     import log_command, trigger_typing, block_dms
from isartbot.database   import Database

from discord.ext import commands
from os.path     import abspath


class Bot(commands.Bot):
    """ Main bot class """

    __slots__ = ("settings", "extensions", "config_file", "database", "logger", "langs", "dev_mode")

    def __init__(self, *args, **kwargs):
        """ Inits and runs the bot """

        self.config_file = abspath('./settings.ini')

        # Setting up logging
        logging.config.fileConfig(self.config_file)
        self.logger = logging.getLogger('isartbot')

        # Loading settings
        self.logger.info('Settings file located at {}'.format(self.config_file))
        self.settings = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
        self.settings.read(self.config_file)

        super().__init__(command_prefix = discord.ext.commands.when_mentioned_or(self.settings.get('common', 'prefix')), *args, **kwargs)

        self.dev_mode   = self.settings.getboolean('debug', 'developement_mode')
        self.extensions = self.settings['extensions']

        # Loading database
        database_name = f"sqlite:///{abspath(self.settings.get('common', 'database'))}"
        self.logger.info(f"Connecting to database {database_name}")
        self.database = Database(self.loop, database_name)

        # Creating the help command
        self.help_command = HelpCommand()

        # Loading languages
        self.langs          = {}
        self.loop.create_task(self.load_languages())
        self.loop.create_task(self.load_extensions())

        # Adding checks
        self.add_check(block_dms      , call_once=True)
        self.add_check(log_command    , call_once=True)
        self.add_check(trigger_typing , call_once=True)

        self.before_invoke(self.fetch_guild_language)

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
                    self.load_extension(f"isartbot.ext.{extension}")
                    self.logger.info   (f"Loaded extension named isartbot.ext.{extension}")
                except Exception as e:
                    self.logger.error(f"Failed to load extension named isartbot.ext.{extension}")
                    await self.on_error(e)
            else:
                self.logger.info(f"Ignored extension named isartbot.ext.{extension}")

        return

    async def load_languages(self):
        """ (re)Loads all the available languages files of the bot"""

        self.langs.clear()

        for (lang, file_name) in self.settings.items("languages"):

            try:
                self.langs[lang] = Lang(file_name)
                self.logger.info(f"Loaded language named {lang} from {file_name}")
            except:
                self.logger.error(f"Failed to load a language")
                await self.on_error(e)

        return

    async def get_translations(self, ctx, keys: list, force_fetch: bool = False):
        """ Returns a set of translations """

        if (force_fetch):
            await self.fetch_guild_language(ctx)

        return dict([(key, self.langs[ctx.guild.description].get_key(key)) for key in keys])

    async def get_translation(self, ctx, key: str, force_fetch: bool = False):
        """ Returns a translation """

        if (force_fetch):
            await self.fetch_guild_language(ctx)

        return self.langs[ctx.guild.description].get_key(key)

    async def register_guild(self, ctx):
        """ Registers the guild into the database, this method is automatically called the first time a command is trigerred in a new guild """

        await self.database.connection.execute(ServerPreferences.table.insert().values(discord_id=ctx.guild.id))
        result = await self.database.connection.execute(ServerPreferences.table.select(ServerPreferences.table.c.discord_id == ctx.guild.id))

        self.logger.warning(f"Registered new discord server to database : '{ctx.guild.name}' id = {ctx.guild.id}")

        return await result.fetchall()

    async def fetch_guild_language(self, ctx):
        """ An event that is called when a command is found and is about to be invoked. """

        # Fetching the guild language and injects it into the context
        result = await self.database.connection.execute(ServerPreferences.table.select(ServerPreferences.table.c.discord_id == ctx.guild.id))
        guilds = await result.fetchall()

        # Checking if the guild is already registered in the database
        if (len(guilds) == 0):
            guilds = await self.register_guild(ctx)

        # We are gonna use the guild description to store the language of the guild
        # since this is not used by discord anyways
        ctx.guild.description = guilds[0][ServerPreferences.table.c.lang]

    # --- Events ---

    async def on_ready(self):
        """
            Executed when the bot is connected
            to discord and ready to operate
        """

        self.logger.info(f"Logged in as {self.user.name}#{self.user.discriminator} - {self.user.id}")

    async def on_command_error(self, ctx, error):
        """ Handles command errors """

        if isinstance(error, UnauthorizedCommand):
            if ctx.channel.permissions_for(ctx.guild.me).send_messages:
                translations = await self.get_translations(ctx, ["failure_title", "unauthorized_command"], force_fetch=True)

                embed = discord.Embed(
                    title       = translations["failure_title"],
                    description = translations["unauthorized_command"].format(error.missing_status),
                    color       = discord.Color.red()
                )

                await ctx.send(embed = embed)

            return

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, (commands.CommandNotFound, commands.UserInputError, commands.CheckFailure)):
            return

        if isinstance(error, commands.MissingPermissions):
            await self.missing_permissions_error(ctx, error)
            return

        # All other Errors not returned come here... And we can just print the default TraceBack.
        self.logger.error(f"Ignoring exception in command \"{ctx.command}\":")

        for err in traceback.format_exception(type(error), error, error.__traceback__):
            index = 0
            for i, char in enumerate(err):
                if (char == '\n'):
                    self.logger.error(err[index:i])
                    index = i + 1

        return

    async def on_error(self, *args, **kwargs):
        """ Sends errors reports """

        self.logger.critical("Unhandled exception occurred:")
        for err in traceback.format_exc().split('\n'):
            self.logger.critical(err)

    async def missing_permissions_error(self, ctx, error):

        embed = discord.Embed()

        embed.title       =    await self.get_translation(ctx, 'error_title')
        embed.description = f"{await self.get_translation(ctx, 'missing_perms_error')} : {error.missing_perms}"
        embed.color       = discord.Color.red()

        await ctx.send(embed=embed)