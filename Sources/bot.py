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
from discord.ext import commands

class Bot(discord.ext.commands.Bot):
    """
    Main bot class.

    """

    def __init__(self, *args, **kwargs):
        """
            Inits the bot
        """

        super().__init__(command_prefix = "!", *args, **kwargs)

        #Private
        self.__settings     = settings.Settings()
        self.__commands     = self.__settings.get("bot", "commands")
        self.__logs         = logs.Logs(self.__settings.get("logs"))
        self.command_prefix = self.__settings.get("bot", "prefix")

        #Setup
        for name, enabled in self.__commands.items():
            if (name != "" and enabled):
                self.load_extension  ('commands.' + name)
                self.__logs.print    ('Loaded the command ' + name)
            else:
                self.__logs.print    ('The command ' + name + ' is currently disabled')
        
        self.add_check(self.globally_block_dms)
        self.run(self.__settings.get("bot", "token"))

    @property
    def settings(self):
        return self.__settings

    async def on_ready(self):
        """
            Executed when the bot is connected
            to discord and ready to operate
        """

        self.__logs.print('Logged in as')
        self.__logs.print('Username : {0}#{1}'.format(self.user.name, self.user.discriminator))
        self.__logs.print('User ID  : {0}'    .format(self.user.id))
        self.__logs.print('------------')

    ###Checks

    async def globally_block_dms(self, ctx):
        """
            Prevents the bot from sending PM's
        """

        return ctx.guild is not None