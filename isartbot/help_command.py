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

import discord

from discord.ext import commands

class HelpCommand(commands.MinimalHelpCommand):

    __slots__ = ("opening_note", "title")

    def __init__(self):

        self.opening_note = ""
        self.title        = "Help"

        super().__init__(verify_checks=True, paginator=commands.Paginator(prefix=None, suffix=None, max_size=1900))

    async def send_pages(self):
        """A helper utility to send the page output from :attr:`paginator` to the destination."""

        destination = self.get_destination()

        for page in self.paginator.pages:
            embed = discord.Embed(
                title       = self.title,
                description = page
            )

            await destination.send(embed=embed)

    async def prepare_help_command(self, ctx, command):
        """ Prepares the help command """

        translations = await self.context.bot.get_translations(self.context, ("help_opening_note", "commands_heading", "help_title"))

        self.opening_note     = translations.pop("help_opening_note", "")
        self.commands_heading = translations.pop("commands_heading" , "")
        self.title            = translations.pop("help_title"       , "Help")

        await super().prepare_help_command(ctx, command)

    def get_opening_note(self):
        """ Returns help command's opening note. This is mainly useful to override for i18n purposes. """

        return self.opening_note.format(self.clean_prefix, self.invoked_with)

    async def send_bot_help(self, mapping):
        """ Sends the global bot help """

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        filtered = await self.filter_commands(self.context.bot.commands)

        self.paginator.add_line('**%s**' % self.commands_heading)
        for command in filtered:
            self.paginator.add_line(f"{self.clean_prefix}{command.name}")

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()

    async def send_cog_help(self, cog):

        bot = self.context.bot

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        if cog.description:
            self.paginator.add_line(await bot.get_translation(self.context, cog.description), empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        if filtered:
            self.paginator.add_line('**%s**' % (self.commands_heading))
            for command in filtered:
                await self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_group_help(self, group):
        """ Sends the command group help """

        await self.add_command_formatting(group)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        if filtered:

            self.paginator.add_line('**%s**' % self.commands_heading)
            for command in filtered:
                await self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_command_help(self, command):
        """ Sends the help command """

        await self.add_command_formatting(command)
        self.paginator.close_page()

        await self.send_pages()

    async def add_command_formatting(self, command):
        """ A utility function to format commands and groups. """

        bot = self.context.bot

        signature = self.get_command_signature(command)
        if command.aliases:
            self.paginator.add_line(signature)
            self.add_aliases_formatting(command.aliases)
        else:
            self.paginator.add_line(signature, empty=True)

        if command.description:
            self.paginator.add_line(await bot.get_translation(self.context, command.description), empty=True)

    async def add_subcommand_formatting(self, command):
        """Adds formatting information on a subcommand."""

        bot  = self.context.bot
        fmt  = '{0}{1} - {2}' if command.short_doc else '{0}{1}'
        line = fmt.format(self.clean_prefix, command.qualified_name, await bot.get_translation(self.context, command.short_doc))

        self.paginator.add_line(line)

    async def command_not_found(self, string):
        """ A method called when a command is not found in the help command. This is useful to override for i18n. """

        return (await self.context.bot.get_translation(self.context, "command_not_found")).format(string)

    async def subcommand_not_found(self, command, string):
        """ A method called when a command did not have a subcommand requested in the help command. This is useful to override for i18n. """

        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            return (await self.context.bot.get_translation(self.context, "no_subcommand_named")).format(command, string)

        return (await self.context.bot.get_translation(self.context, "no_subcommand")).format(command)