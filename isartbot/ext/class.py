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
from isartbot.checks     import is_moderator

class ClassExt (commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    def get_class(self, ctx, class_name: upper_clean):
        """ Checks if a class exists or not """

        prefix = ctx.bot.settings.get("class", "delegate_role_prefix")

        role          = discord.utils.get(ctx.guild.roles, name=class_name)
        delegate_role = discord.utils.get(ctx.guild.roles, name=f'{prefix} {class_name}')

        return role, delegate_role

    @commands.group(pass_context=True, invoke_without_command=True, 
                    help="class_help", description="class_description", 
                    name="class")
    @commands.check(is_moderator)
    async def _class(self, ctx):
        """Class modification command"""

        if ctx.invoked_subcommand is None:
            await ctx.send(await ctx.bot.get_translation(ctx, 'class'))

    @_class.command(help="class_create_help", description="class_create_description")
    @commands.check(is_moderator)
    async def create(self, ctx, name: upper_clean):
        """Creates a class"""

        role, delegate = self.get_class(ctx, name)

        #Checking if the roles/channels already exists
        if role is not None or delegate is not None:
            await ctx.bot.send_fail(ctx, "This class already exists!", "Error")
            return

    @_class.command(help="class_delete_help", description="class_delete_description")
    @commands.check(is_moderator)
    async def delete(self, ctx, name: upper_clean):
        """Deletes a class"""

    @_class.command(help="class_rename_help", description="class_rename_description")
    @commands.check(is_moderator)
    async def rename(self, ctx, name: upper_clean):
        """Renames a class"""

def setup(bot):
    bot.add_cog(ClassExt(bot))
