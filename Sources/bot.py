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

class Bot(discord.Client):
    """
    Main bot class.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Public
        self.settings = settings.Settings()
        self.logs     = logs.Logs(self.settings.get("logs"))

        #Setup
        self.run(self.settings.get("bot", "token"))

    async def on_ready(self):
        self.logs.print('Logged in as')
        self.logs.print('Username : {0}#{1}'.format(self.user.name, self.user.discriminator))
        self.logs.print('User ID  : {0}'    .format(self.user.id))
        self.logs.print('------------')