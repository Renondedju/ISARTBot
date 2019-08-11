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

    __slots__ = ("opening_note")

    def __init__(self, **options):

        self.opening_note = ""

        # Forcing the checks verification
        options['verify_checks'] = True
        
        super().__init__(**options)

    async def prepare_help_command(self, ctx, command):
        """ Prepares the help command """

        self.opening_note     = await self.context.bot.get_translation(self.context, "help_opening_note")
        self.commands_heading = await self.context.bot.get_translation(self.context, "commands_heading")

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

    async def send_group_help(self, group):
        self.add_command_formatting(group)

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        if filtered:
            note = self.get_opening_note()
            if note:
                self.paginator.add_line(note, empty=True)

            self.paginator.add_line('**%s**' % self.commands_heading)
            for command in filtered:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_command_help(self, command):
        self.add_command_formatting(command)
        self.paginator.close_page()
        await self.send_pages()