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
import asyncio

from discord.ext         import commands
from isartbot.converters import upper_clean

class Iam_commands():
    """ Role assignment class """

    def __init__(self, bot):

        #Private
        self.bot = bot

    @commands.command(pass_context=True)
    async def iam(self, ctx, class_name : upper_clean):
        """ Assign a class role to a user"""

        role_names = self.bot.settings.get('roles', command = 'iam')

        #Checking if the requested role exists 
        if class_name not in role_names:
            await self.bot.send_fail(ctx,
                "This class doesn't exists !", "I am")
            return

        #Checking if the user has already a class role
        author_role_names = (role.name for role in ctx.author.roles)
        if class_name in author_role_names:
            await self.bot.send_fail(ctx,
                "You already have a class role", "I am")
            return

        id = self.bot.settings.get('isartian_role_id', command='iam')
        
        await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, name=class_name))
        await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, id  = id))

        await self.bot.send_success(ctx, "Role added !", "I am")

def setup(bot):
    bot.add_cog(Iam_commands(bot))