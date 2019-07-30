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

from   discord.ext import commands
from   os.path     import abspath

class Bot(discord.ext.commands.Bot):
    """ Main bot class """

    __slots__ = ("settings", "modules", "config_file")

    def __init__(self, *args, **kwargs):
        """ Inits and runs the bot """

        super().__init__(command_prefix = "!", *args, **kwargs)

        self.config_file = abspath('./settings.ini')

        # Setting up loggign
        logging.config.fileConfig(self.config_file)
        self.logger = logging.getLogger('isartbot')

        # Loading settings
        self.logger.info('Settings file located at {}'.format(self.config_file))
        self.settings = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
        self.settings.read(abspath('./settings.ini'))

        self.modules        = self.settings['modules']
        self.command_prefix = self.settings.get('common', 'prefix')

        self.run(self.settings.get('common', 'token'))


#        #setting up logger
#       logging.basicConfig(
#           level=logging.INFO,
#           format="%(asctime)s - [%(levelname)s] %(message)s",
#           datefmt="%Y-%m-%d %H:%M:%S",
#           handlers=[
#               logging.StreamHandler(sys.stdout),
#               logging.FileHandler("logs.log", mode='a', encoding=None, delay=False)
#           ]
#       )