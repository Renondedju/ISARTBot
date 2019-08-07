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

import asyncio

from sqlalchemy_aio     import ASYNCIO_STRATEGY
from sqlalchemy         import create_engine
from sqlalchemy.schema  import CreateTable

from isartbot.models import ServerPreferences

class Database:

    __slots__ = ("engine", "connection", "loop")

    def __init__(self, loop, database_name: str):
        
        self.loop       = loop
        self.engine     = create_engine(database_name, strategy=ASYNCIO_STRATEGY)
        self.connection = None

        self.loop.run_until_complete(self.init())

    def __del__(self): 
        
        self.loop.run_until_complete(self.cleanup())

    #TODO Add table sync
    async def init(self):
        """ Inits the database connection """

        #await self.engine.execute(CreateTable(ServerPreferences.table))

        self.connection = await self.engine.connect()

    async def cleanup(self):
        """ Cleanups the database connection """
        
        await self.connection.close()

        