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

import discord

from isartbot import Bot

class Assignable_role():

    def __init__(self, bot, json : dict):

        self.bot = bot

        self.role         = self.convert_role(json.get('id', 0))
        self.dependencies = self.convert_list(json.get('dependencies', []))
        self.conflicting  = self.convert_list(json.get('conflicting' , []))

    @property
    def json(self):
        """ Returns a json representation of the object """
        return  {
                    "id"          : self.role.id,
                    "dependencies": [role.id for role in self.dependencies],
                    "conflicting" : [role.id for role in self.conflicting]
                }

    def convert_list(self, ids : list) -> set:
        """ Converts a list of ids to a list or roles """
        roles = set()

        for id in ids:
            role = self.convert_role(id)
            if role != None:
                roles.add(role)

        return roles

    def convert_role(self, id  : int ) -> discord.Role:
        """ Convert an id to a role """

        return discord.utils.get(self.bot.guild.roles, id = id)
    