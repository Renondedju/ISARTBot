"""
@author : Basile Combet
@brief  : Bot class file

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