"""
@author : Basile Combet
@brief  : Bot class file

"""

#Importing discord libraries (local)
import sys
sys.path.insert(0, "./Lib/discord.py")

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

        self.settings = settings.Settings()

        self.run(self.settings.get("bot", "token"))

    async def on_ready(self):
        print('Logged in as')
        print('Username : {0}#{1}'.format(self.user.name, self.user.discriminator))
        print('User ID  : {0}'    .format(self.user.id))
        print('------')