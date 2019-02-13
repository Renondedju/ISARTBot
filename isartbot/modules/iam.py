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

import re
import discord
import asyncio
import itertools

from typing                        import Union, List
from discord.ext                   import commands
from isartbot.converters           import upper_clean
from isartbot.bot_decorators       import is_admin
from isartbot.data.assignable_role import *

class Iam_commands():
    """ Role assignment class """

    def __init__(self, bot):

        #Private
        self.bot = bot

    @commands.command(pass_context=True)
    async def iam(self, ctx, role : discord.Role):
        """ Adds a role to a user"""

        assignable_roles = get_self_assignable_roles(self.bot)

        #For every assignable role
        for assignable_role in assignable_roles:

            #If we found the desired role
            if role.id == assignable_role.role.id:
                await ctx.author.add_roles(role, reason = 'Requested via an iam command')
                return await self.bot.send_success(ctx, "Role added!", "I am")

        return await self.bot.send_fail(ctx, "You cannot assing yourself this role!", "I am")

    @commands.command(pass_context=True)
    async def iamn(self, ctx, role : discord.Role):
        """ Removes a role from a user"""

        assignable_roles = get_self_assignable_roles(self.bot)

        #For every assignable role
        for assignable_role in assignable_roles:

            #If we found the desired role
            if role.id == assignable_role.role.id:
                await ctx.author.remove_roles(role, reason = 'Requested via an iamn command')
                return await self.bot.send_success(ctx, "Role removed!", "I am")

        return await self.bot.send_fail(ctx, "This role isn't a self assignable role!", "I am")

    @commands.command(pass_context=True, hidden=True, name='as')
    @commands.check(is_admin)
    async def _as(self, ctx, member : discord.Member, *, command_str : str):

        prefix = self.bot.settings.get('bot', 'prefix')
        regex  = r"{0}(\w*)\s.*".format(prefix)
        matches = re.search(regex, command_str)

        if not matches:
            await self.bot.send_fail(ctx, 'There is no command to invoke.')
            return

        command = self.bot.get_command(matches.group(1))
        if (not await command.can_run(ctx)):
            await self.bot.send_fail(ctx, 
                                "The checks for this command failed, "
                                "maybe you don't have the required rights ?")
            return

        for word in re.compile('\w+').findall(command_str.replace(prefix + matches.group(1), '')):

            # if type of 'command' is a discord command, then everything is ready to be executed
            if type(command) == discord.ext.commands.core.Command:
                break

            command = command.get_command(word)
            if command is None:
                break
            if (not await command.can_run(ctx)):
                await self.bot.send_fail(ctx,
                                "The checks for this subcommand failed, "
                                "maybe you don't have the required rights ?")
                return

        msg: discord.Message = await ctx.send(command_str)
        msg.author           = member
        await self.bot.process_commands(msg)

        return

    @_as.error
    async def _as_error(self, ctx, error):

        if isinstance(error, commands.CheckFailure):
            try:
                await ctx.bot.send_fail(ctx, "You need to be an admin to use this command")
            except:
                pass

        await ctx.bot.on_error(ctx, error)

    @commands.command(pass_context=True, hidden=True, name='for',
        usage="!for <Users and/or Roles> <'add' or 'remove'> <Roles>")
    @commands.check(is_admin)
    async def _for(self, ctx, *args : Union[discord.Member, discord.Role, str]):
        """ Removes or adds roles to members of the guild """
        selectors, action, roles = [list(items) for _, items in itertools.groupby(args, key=lambda x: isinstance(x, str))]

        if len(action) != 1:
            await self.bot.send_fail(ctx, "Action should be 'add' or 'remove'!", 'Error')
            return

        action = action[0].lower()

        if action not in ['add', 'remove']:
            await self.bot.send_fail(ctx, "Action should be 'add' or 'remove'!", 'Error')
            return

        selected_members = set()

        for selection in selectors:
            if isinstance(selection, discord.Member):
                selected_members.add(selection)
                continue
            
            for member in selection.members:
                selected_members.add(member)

        async def add():
            for member in selected_members:
                for role in roles:
                    await member.add_roles(role)
        
        async def remove():
            for member in selected_members:
                for role in roles:
                    await member.remove_roles(role)

        strategies = {'add' : add, 'remove' : remove}

        await strategies[action]()

        await self.bot.send_success(ctx,
            'Used the \'{}\' strategy with the roles {} on {}'.format(
                action,
                ' '.join([role.mention for role in roles]),
                ' '.join([selector.mention for selector in selectors])),
            'For command')

    @_for.error
    async def _for_error(self, ctx, error):

        if isinstance(error, commands.CheckFailure):
            try:
                await ctx.bot.send_fail(ctx, "You need to be an admin to use this command")
            except:
                pass

        await ctx.bot.on_error(ctx, error)

    @commands.command(pass_context=True, hidden=True)
    @commands.check(is_admin)
    async def asar(self, ctx, role: discord.Role):
        """ asar stand for 'Add Self Assignable Role' """

        if role is None:
            return await self.bot.send_fail(ctx, 
                "The role you asked for does not exists",
                "Add self assignable role")

        if not save_self_assignable_role(self.bot, Assignable_role(self.bot, role)):
            return await self.bot.send_fail(ctx,
                f"Failed to add the role {role.mention} as a self assignable role.",
                "Add self assignable role")

        return await self.bot.send_success(ctx,
            f"Role successfully added {role.mention} to the self assignable roles",
            "Add self assignable role")

    @commands.command(pass_context=True, hidden=True)
    @commands.check(is_admin)
    async def rsar(self, ctx, role: discord.Role):
        """ rsar stands for 'Remove Self Assignable Role' """

        if remove_self_assignable_role(self.bot, role):
            return await self.bot.send_success(ctx,
                "Role successfully removed!",
                "Remove self assignable role")

        return await self.bot.send_fail(ctx,
                "No such role to remove!",
                "Remove self assignable role")

def setup(bot):
    bot.add_cog(Iam_commands(bot))