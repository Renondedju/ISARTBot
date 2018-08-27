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

    def __init__(self, bot, json : dict = {}):

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

    def set_role(self, role: Union[int, discord.Role]):
        """ Sets the main role """

        if isinstance(role, int):
            self.role = self.convert_role(role)
            return

        self.role = role
        return

    def add_dependency(self, role: Union[int, discord.Role]) -> bool:
        """ Adds a role dependency """

        if isinstance(role, int):
            return self.__add_item_id(role, 'dependencies')

        return self.__add_item_role(role, 'dependencies')

    def add_conflicting(self, role: Union[int, discord.Role]) -> bool:
        """ Adds a conflicting role """

        if isinstance(role, int):
            return self.__add_item_id(role, 'conflicting')

        return self.__add_item_role(role, 'conflicting')

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
    
    def __add_item_id(self, id: int, item: str) -> bool:
        """ Adds a new dependency role via id
            returns True if the operation is successful
        """

        role = self.convert_role(id)
        if role == None:
            return False

        getattr(self, item).add(role)
        return True

    def __add_item_role(self, role: discord.Role, item: str) -> bool:
        """ Adds a new dependency role
            returns True if the operation is successful
        """

        if role == None:
            return False

        getattr(self, item).add(role)
        return True

def create_self_assignable_role(bot,
                                role        :      Union[int, discord.Role],
                                dependencies: List[Union[int, discord.Role]] = [],
                                conflicts   : List[Union[int, discord.Role]] = []) -> Assignable_role:
    """ Creates a self assignable role """

    clean_self_assignable_roles(bot)
    assignable_role = Assignable_role(bot)

    assignable_role.set_role(role)

    for dependency in dependencies:
        assignable_role.add_dependency(dependency)

    for conflict in conflicts:
        assignable_role.add_conflicting(conflict)

    return assignable_role

def clean_self_assignable_roles(bot):
    """ Cleans every self assignable role (And deletes them if needed)"""

    #Since a lot of functions uses this one, to prevent infinite loops from happening
    #We are inspecting the call stack and returning here if another instance of this function
    #is noticed.

    call_count = 0
    for call in inspect.stack():
        if call.function == 'clean_self_assignable_roles':
            call_count += 1
        if call_count >= 2:
            return

    #For every assignable role
    for raw_role in bot.settings.get('assignable_roles', command = 'iam'):

        role = Assignable_role(bot, raw_role)

        #If the main role does not exists anymore : removing the assignable role
        if role.role is None:
            remove_self_assignable_role(bot, raw_role.get('id', 0))
            bot.logs.print('Automatically removed from self assignable roles: id = {}'
                .format(raw_role.raw_role.get('id', 0)))
            continue

        #Removing from the dependencies and conflicting roles everything that is None
        role.dependencies = set((role for role in role.dependencies if role != None))
        role.conflicting  = set((role for role in role.conflicting  if role != None))

    return

def convert_assignable_roles_to_json(assignable_roles: List[Assignable_role]) -> List[dict]:
    """ Converts a list of assignable roles to a json representation of them """

    json = []

    for role in assignable_roles:
        json.append(role.json)

    return json

def save_self_assignable_role(bot, assignable_role: Assignable_role) -> bool:
    """ Saves a self assignable role into the 'iam/assignable_roles' settings 
        Returns true if the operation was successful, False otherwise
    """
    if assignable_role is None or bot is None:
        return False

    clean_self_assignable_roles(bot)
    assignable_roles = get_self_assignable_roles(bot)

    for role in assignable_roles:
        if assignable_role.role.id == role.role.id:
            return False

    assignable_roles.append(assignable_role)

    bot.settings.write(convert_assignable_roles_to_json(assignable_roles), 
        'assignable_roles', command = 'iam')
    return True

def remove_self_assignable_role(bot, role: Union[int, discord.Role]) -> bool:
    """ Removes an assignable role from the list
        Returns True if the operation has been successful, False otherwise
    """

    clean_self_assignable_roles(bot)

    if role == None:
        return False

    #If the role isn't an int, using its id to make it an int
    if isinstance(role, discord.Role):
        role = role.id
    
    raw_roles = bot.settings.get('assignable_roles', command = 'iam')
    new_roles = [json for json in raw_roles if json.get('id', 0) != role]
    bot.settings.write(new_roles, 'assignable_roles', command = 'iam')

    return True

def get_self_assignable_role(bot, role: Union[int, discord.Role]) -> Assignable_role:
    """ Gets an assignable role from a role id or a discord.Role
        Returns None if nothing has been found
    """

    clean_self_assignable_roles(bot)

    if role == None:
        return None

    id = role
    if isinstance(role, discord.Role):
        id = role.id

    assignable_roles = get_self_assignable_roles(bot)

    for assignable_role in assignable_roles:
        if assignable_role.role is None:
            return None

        if assignable_role.role.id == id:
            return assignable_role

    return None

def get_self_assignable_roles(bot) -> List[Assignable_role]:
    """ Returns every assignable role """

    clean_self_assignable_roles(bot)

    assignable_roles_raw = bot.settings.get('assignable_roles', command = 'iam')
    return [Assignable_role(bot, json) for json in assignable_roles_raw]