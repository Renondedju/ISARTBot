# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018-2020 Renondedju

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

from isartbot.lang         import Lang
from isartbot.checks       import log_command, trigger_typing, block_dms
from isartbot.database     import Server, Database
from isartbot.exceptions   import UnauthorizedCommand, VerificationRequired
from isartbot.help_command import HelpCommand

from os.path     import abspath
from discord.ext import commands


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
        self.settings.read(self.config_file, encoding='utf-8')

        intents = discord.Intents()
        intents.guild_reactions = True
        intents.guild_messages  = True
        intents.presences       = True
        intents.members         = True
        intents.emojis          = True
        intents.guilds          = True

        super().__init__(command_prefix = discord.ext.commands.when_mentioned_or(self.settings.get('common', 'prefix')), intents = intents, *args, **kwargs)

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

        token = configparser.ConfigParser()
        token.read(abspath('./token.ini'), encoding='utf-8')
        self.run(token.get('DEFAULT', 'token'))

    async def load_extensions(self):
        """ Loads all the cogs of the bot defined into the settings.ini file """

        try:
            await self.wait_for("ready", timeout=30)
            self.logger.info("Loading extensions...")
        except asyncio.futures.TimeoutError:
            self.logger.warning("Wait for on_ready event timed out, loading the extensions anyway...")

        for (extension, _) in self.settings.items("extensions"):
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
            except Exception as e:
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

    def register_guild(self, guild: discord.Guild):
        """ Registers the guild into the database, this method is automatically called the first time a command is trigerred in a new guild """

        new_server_preferences = Server(discord_id=guild.id)

        self.database.session.add(new_server_preferences)
        self.database.session.commit()

        self.logger.warning(f"Registered new discord server to database : '{guild.name}' id = {guild.id}")

        return new_server_preferences

    async def fetch_guild_language(self, ctx):
        """ An event that is called when a command is found and is about to be invoked. """

        # Fetching the guild language and injects it into the context
        lang = self.database.session.query(Server.lang).\
            filter(Server.discord_id == ctx.guild.id).first()

        # Checking if the guild is already registered in the database
        if (lang == None):
            lang = (self.register_guild(ctx.guild)).lang
        else:
            lang = lang[0]

        # We are gonna use the guild description to store the language of the guild
        # since this is not used by discord anyways
        ctx.guild.description = lang

    # --- Events ---

    async def on_ready(self):
        """
            Executed when the bot is connected
            to discord and ready to operate
        """

        self.logger.info(f"Logged in as {self.user.name}#{self.user.discriminator} - {self.user.id}")

    async def on_connect(self):
        """Executed when the bot connects to discord"""

        self.logger.info("Discord connection established")

    async def on_disconnect(self):
        """Executed when the bot connects to discord"""

        self.logger.info("Discord connection terminated")

    async def on_guild_join(self, guild: discord.Guild):
        """Called when a Guild is either created by the Client or when the Client joins a guild"""

        self.logger.warning(f"Joined guild : {guild.name}")
        self.register_guild(guild)

    async def on_guild_remove(self, guild: discord.Guild):
        """Called when a Guild is removed from the Client"""
        
        self.logger.warning(f"Left guild : {guild.name}")

        # Server should always be valid
        server = self.database.session.query(Server).filter(Server.discord_id == guild.id).first()

        if (server != None):
            self.database.session.delete(server)
            self.database.session.commit()
        else:
            self.logger.warning(f"No database entry found for the guild named {guild.name} (id = {guild.id})")

    async def on_command_error(self, ctx, error):
        """ Handles command errors """

        if isinstance(error, UnauthorizedCommand):
            await self.unauthorized_command_error(ctx, error)
            return

        if isinstance(error, VerificationRequired):
            await self.verification_required_error(ctx, error)
            return

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, (commands.CommandNotFound, commands.CheckFailure)):
            return

        if isinstance(error, commands.UserInputError):
            await ctx.send_help(ctx.command)
            return

        if isinstance(error, commands.MissingPermissions):
            await self.missing_permissions_error(ctx, error)
            return

        if isinstance(error, commands.BotMissingPermissions):
            await self.bot_missing_permissions_error(ctx, error)
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

    async def unauthorized_command_error(self, ctx, error):
        """ Sends a missing permission error """

        self.logger.info(f"Access unauthorized, command has been denied.")
        if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
            return

        translations = await self.get_translations(ctx, ["failure_title", "unauthorized_command"], force_fetch=True)

        embed = discord.Embed(
            title       = translations["failure_title"],
            description = translations["unauthorized_command"].format(error.missing_status),
            color       = discord.Color.red()
            )

        await ctx.send(embed = embed)

    async def missing_permissions_error(self, ctx, error):
        """ Sends a missing permission error """

        if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
            return

        translations = await self.get_translations(ctx, ["failure_title", "missing_perms_error"], force_fetch=True)

        embed = discord.Embed(
            title       = translations["failure_title"],
            description = translations["missing_perms_error"].format(error.missing_perms),
            color       = discord.Color.red()
        )

        await ctx.send(embed=embed)

    async def bot_missing_permissions_error(self, ctx, error):
        """ Sends a missing permission error """

        if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
            return

        translations = await self.get_translations(ctx, ["failure_title", "bot_missing_perms_error"], force_fetch=True)

        embed = discord.Embed(
            title       = translations["failure_title"],
            description = translations["bot_missing_perms_error"].format(error.missing_perms),
            color       = discord.Color.red()
        )

        await ctx.send(embed=embed)

    async def verification_required_error(self, ctx, error):
        """ Sends a verification required error """

        if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
            return

        translations = await self.get_translations(ctx, ["failure_title", "verified_role_required"], force_fetch=True)

        embed = discord.Embed(
            title       = translations["failure_title"],
            description = translations["verified_role_required"].format(error.missing_role),
            color       = discord.Color.red()
        )

        await ctx.send(embed=embed)