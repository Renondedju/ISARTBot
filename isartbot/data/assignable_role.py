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
import inspect

from typing   import Union, List
from isartbot import Bot

class Assignable_role():

    def __init__(self, bot, role: Union[int, discord.Role]):

        self.bot  = bot
        self.role = 0

        self.set_role(role)

    def set_role(self, role: Union[int, discord.Role]):
        """ Sets the main role """

        if isinstance(role, int):
            self.role = self.convert_role(role)
            return

        self.role = role
        return

    def convert_list(self, ids : list) -> set:
        """ Converts a list of ids to a list of roles """
        roles = set()

        for id in ids:
            role = self.convert_role(id)
            if role != None:
                roles.add(role)

        return roles

    def convert_role(self, id  : int ) -> discord.Role:
        """ Convert an id to a role """

        return discord.utils.get(self.bot.guild.roles, id = id)

def save_self_assignable_role(bot, assignable_role: Assignable_role) -> bool:
    """ Saves a self assignable role into the 'iam/assignable_roles' settings 
        Returns true if the operation was successful, False otherwise
    """
    if assignable_role is None or bot is None:
        return False
    
    # Fetching the current roles
    raw_roles = bot.settings.get('assignable_roles', command = 'iam')

    #Checking if the role is already in there
    for role in raw_roles:
        if int(role) == int(assignable_role.role.id):
            return False

    #If not, adding it to the list
    raw_roles.append(int(assignable_role.role.id))

    #Writing the new role list
    bot.settings.write(raw_roles, 'assignable_roles', command = 'iam')

    return True

def remove_self_assignable_role(bot, role: Union[int, discord.Role]) -> bool:
    """ Removes an assignable role from the list
        Returns True if the operation has been successful, False otherwise
    """

    if role == None:
        return False

    #If the role isn't an int, using its id to make it an int
    if isinstance(role, discord.Role):
        role = role.id
    
    raw_roles = bot.settings.get('assignable_roles', command = 'iam')
    new_roles = [int(id) for id in raw_roles if int(id) != int(role)]
    bot.settings.write(new_roles, 'assignable_roles', command = 'iam')

    return True

def get_self_assignable_role(bot, role: Union[int, discord.Role]) -> Assignable_role:
    """ Gets an assignable role from a role id or a discord.Role
        Returns None if nothing has been found
    """

    if role == None:
        return None

    id = role
    if isinstance(role, discord.Role):
        id = role.id

    assignable_roles = get_self_assignable_roles(bot)

    for assignable_role in assignable_roles:
        if assignable_role.role.id == id:
            return assignable_role

    return None

def get_self_assignable_roles(bot) -> List[Assignable_role]:
    """ Returns every assignable role """

    assignable_roles_raw = bot.settings.get('assignable_roles', command = 'iam')
    return [Assignable_role(bot, id) for id in assignable_roles_raw]