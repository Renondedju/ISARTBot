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

from isartbot                      import Bot
from isartbot.data.classtype       import Class_type
from isartbot.data.assignable_role import *


class Data_class():

    def __init__(self, bot : Bot, name : str):

        self.name              = self.get_name(name)
        self.role              = self.get_role()
        self.delegate_role     = self.get_delegate_role()
        self.category          = self.get_category()
        self.type              = self.eval_type()
        self.bot               = bot

    def get_name(self, name : str) -> str:
        """ Retruns the cleaned name of the class """

        return name.upper().strip()

    def get_role(self) -> discord.Role:
        """ Returns the main name of the class """

        return discord.utils.get(self.bot.guild.roles, name = self.name)

    def get_category(self) -> discord.CategoryChannel:
        """ Returns the category channel of the class """

        return discord.utils.get(self.bot.guild.categories, name = self.get_name(self.name))

    def get_delegate_role(self) -> discord.Role:
        """ Returns the delegate role of the class"""

        delegate_prefix = self.bot.settings.get('delegate_role_prefix', command='class')
        return discord.utils.get(self.bot.guild.roles, name = delegate_prefix + ' ' + self.name)

    def eval_type(self) -> Class_type:
        """ Evaluates the class type from the class name (may not be 100% accurate !) """

        #Getting the name of every class type from the classtype enum
        instance = Class_type()
        members = [attr for attr in dir(instance) if not callable(getattr(instance, attr)) and not attr.startswith("__")]

        selected_member = ''
        # Looking for a member
        for member in members:
            if member.upper() in self.get_name(self.name) and len(selected_member) < len(member):
                selected_member = member

        #Returning the right selected member.
        #If none has been found, returning Class_type.none
        try:
            return getattr(Class_type, selected_member)
        except:
            pass

        return Class_type.none

    def add_assignable_role(self) -> bool:
        """ Adds an assignable role corresponding to the class role 
            Returns true if the operation is successful 
        """

        iartian_role_id = self.bot.settings.get('bot', 'isartian_role_id')
        role_type       = discord.utils.get(self.bot.guild.roles, name = self.typename)

        assignable_role = create_self_assignable_role(self.bot, 
            self.role,                               # Main role
            [iartian_role_id, self.typename],        # Dependencies
            [iartian_role_id, self.role, role_type]) # Conflicting roles  


        return save_self_assignable_role(self.bot, assignable_role)

    def remove_assignable_role(self) -> bool:
        """ Removes the assignable role for this class
            Returns True if the operation is successful
        """

        return remove_self_assignable_role(self.bot, self.role)

    @property
    def typename(self):

        #Getting the name of every class type from the classtype enum
        instance = Class_type()
        members = [attr for attr in dir(instance) if not callable(getattr(instance, attr)) and not attr.startswith("__")]

        for member in members:
            try:
                attribute = getattr(Class_type, member)
            except:
                return ""
                
            if attribute == self.type:
                return member

        return ""
