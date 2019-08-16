# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018 - 2019 Renondedju, Torayl

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
import re
import io

from discord.ext     import commands
from isartbot.checks import is_moderator
from discord.abc     import Messageable

class ModerationExt(commands.Cog):
    """Helps with moderation"""

    def __init__(self, bot):

        #Private
        self.bot = bot

    async def error_embed(self, ctx, description: str, *args):
        """Create an error embed"""

        return discord.Embed(
            title       = await ctx.bot.get_translation(ctx, "failure_title"),
            description = (await ctx.bot.get_translation(ctx, description)).format(*args),
            color       = discord.Color.red())

    async def success_embed(self, ctx, description: str, *args):
        """Create a success embed"""

        return discord.Embed(
            title       = await ctx.bot.get_translation(ctx, 'success_title'),
            description = (await ctx.bot.get_translation(ctx, description)).format(*args),
            color       = discord.Color.green())

    @commands.group(pass_context=True)
    @commands.check(is_moderator)
    async def mod(self, ctx):
        pass


    #Prune command
    @mod.command(help="mod_prune_help", description="mod_prune_description")
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    @commands.has_permissions    (manage_messages=True, read_message_history=True)
    async def prune(self, ctx, number: int, member: discord.Member = None):
        """Deletes a certain amount of the latest messages in this text channel"""

        embed = discord.Embed()
        messages = []
        if (member is None):
            embed = await self.success_embed(ctx, 'success_prune_message', number)
            messages = await ctx.channel.history(limit=number + 1).flatten()
        else:
            async for message in ctx.channel.history(limit=number + 1):
                if (message.author == member):
                     messages.append(message)
            messages.append(ctx.message)
            embed = await self.success_embed(ctx, 'success_prune_member', number, member.mention)

        await ctx.channel.delete_messages(set(messages))
            
        await ctx.send(embed=embed, delete_after=5.0)

    #Kick command
    @mod.command(help="mod_kick_help", description="mod_kick_description")
    @commands.bot_has_permissions(kick_members=True)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="Because"):
        """Kicks a member"""

        #await member.kick(reason=reason)

        file = discord.File("isartbot/media/kick.gif", filename="kick.gif")
        embed = await self.success_embed(ctx, 'success_kick', member.mention, ctx.author.mention, reason)
        embed.set_image(url="attachment://kick.gif")

        self.bot.logger.warning((await ctx.bot.get_translation(ctx, 'success_kick')).format(member.name, ctx.author.name, reason))

        await ctx.send(file=file, embed=embed)

    #Ban command
    @mod.command(aliases=["banhammer", "derive_autoritaire"], help="mod_ban_help", description="mod_ban_description")
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="Nothing special"):
        """Bans a member"""

        await member.ban(reason=reason, delete_message_days=0)

        fileHammer = discord.File("isartbot/media/banhammer.gif", filename="banhammer.gif")
        fileSalty = discord.File("isartbot/media/saltyban.gif", filename="saltyban.gif")
        
        embed = await self.success_embed(ctx, 'success_ban', member.mention, ctx.author.mention, reason)
        embed.set_image(url="attachment://banhammer.gif")

        if (ctx.invoked_with == 'derive_autoritaire'):
            embed.set_image(url="attachment://saltyban.gif")
            await ctx.send(file=fileSalty, embed=embed)
        else:
            embed.set_image(url="attachment://banhammer.gif")
            await ctx.send(file=fileHammer, embed=embed)

        self.bot.logger.warning((await ctx.bot.get_translation(ctx, 'success_ban')).format(member.name, ctx.author.name, reason))

#    @commands.command(help="mod_as_help", description="mod_as_description", name='as')
#    @commands.check(is_moderator)
#    async def _as(self, ctx, member : discord.Member, *, command_str : str):
#
#        prefix = self.bot.clean_prefix
#        regex  = r"{0}(\w*)\s.*".format(prefix)
#        matches = re.search(regex, command_str)
#
#        embedFail = discord.Embed()
#        embedFail.title = "Failed"
#        embedFail.colour = discord.Color.red()
#
#        if not matches:
#            embedFail.description = 'There is no command to invoke.'
#            await ctx.send(embed=embed)
#            return
#
#        command = self.bot.get_command(matches.group(1))
#        if (not await command.can_run(ctx)):
#            embedFail.description = "The checks for this command failed, "
#                                    "maybe you don't have the required rights ?"
#            await ctx.send(embed=embed)
#            return
#
#        for word in re.compile('\w+').findall(command_str.replace(prefix + matches.group(1), '')):
#
#            # if type of 'command' is a discord command, then everything is ready to be executed
#            if type(command) == discord.ext.commands.core.Command:
#                break
#
#            command = command.get_command(word)
#            if command is None:
#                break
#            if (not await command.can_run(ctx)):
#                await self.bot.send_fail(ctx,
#                                "The checks for this subcommand failed, "
#                                "maybe you don't have the required rights?")
#                return
#
#        msg: discord.Message = await ctx.send(command_str)
#        msg.author           = member
#        await self.bot.process_commands(msg)
#
#        return
#
#    @commands.command(pass_context=True, hidden=True, name='for',
#        usage="!for <Users and/or Roles> <'add' or 'remove'> <Roles>")
#    @commands.check(is_admin)
#    async def _for(self, ctx, *args : Union[discord.Member, discord.Role, str]):
#        """Removes or adds roles to members of the guild"""
#        selectors, action, roles = [list(items) for _, items in itertools.groupby(args, key=lambda x: isinstance(x, str))]
#
#        if len(action) != 1:
#            await self.bot.send_fail(ctx, "Action should be 'add' or 'remove'!", 'Error')
#            return
#
#        action = action[0].lower()
#
#        if action not in ['add', 'remove']:
#            await self.bot.send_fail(ctx, "Action should be 'add' or 'remove'!", 'Error')
#            return
#
#        selected_members = set()
#
#        for selection in selectors:
#            if isinstance(selection, discord.Member):
#                selected_members.add(selection)
#                continue
#
#            for member in selection.members:
#                selected_members.add(member)
#
#        async def add():
#            for member in selected_members:
#                for role in roles:
#                    await member.add_roles(role)
#
#        async def remove():
#            for member in selected_members:
#                for role in roles:
#                    await member.remove_roles(role)
#
#        strategies = {'add' : add, 'remove' : remove}
#
#        await strategies[action]()
#
#        await self.bot.send_success(ctx,
#            'Used the \'{}\' strategy with the roles {} on {}'.format(
#                action,
#                ' '.join([role.mention for role in roles]),
#                ' '.join([selector.mention for selector in selectors])),
#            'For command')

def setup(bot):
    bot.add_cog(ModerationExt(bot))
