# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018 - 2019 Renondedju

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

from typing              import Union
from itertools           import groupby
from discord.ext         import commands
from isartbot.helper     import Helper
from isartbot.checks     import is_moderator
from isartbot.converters import MemberConverter

class ModerationExt(commands.Cog):
    """Helps with moderation"""

    def __init__(self, bot):
        self.bot = bot

    async def error_embed(self, ctx, description: str, *args):
        """Create an error embed"""

        return discord.Embed(
            title       =  await ctx.bot.get_translation(ctx, "failure_title"),
            description = (await ctx.bot.get_translation(ctx, description)).format(*args),
            color       = discord.Color.red())

    async def success_embed(self, ctx, description: str, *args):
        """Create a success embed"""

        return discord.Embed(
            title       =  await ctx.bot.get_translation(ctx, 'success_title'),
            description = (await ctx.bot.get_translation(ctx, description)).format(*args),
            color       = discord.Color.green())

    @commands.group(pass_context=True, invoke_without_command=True,
        help="mod_help", description="mod_description")
    @commands.check(is_moderator)
    async def mod(self, ctx):
        await ctx.send_help(ctx.command)

    @mod.command(help="mod_prune_help", description="mod_prune_description")
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    @commands.has_permissions    (manage_messages=True, read_message_history=True)
    async def prune(self, ctx, number: int, member: discord.Member = None):
        """Deletes a certain amount of the latest messages in this text channel"""

        messages = []
        if (member is None):
            messages = await ctx.channel.history(limit=number).flatten()

        else:
            async for message in ctx.channel.history(limit=number):
                if (message.author == member):
                    messages.append(message)

        if (len(messages) > 100):
            await Helper.send_error(ctx, ctx.channel, "fail_prune_size", format_content=(len(messages),))
            return

        try: 
            await ctx.channel.delete_messages(messages)
        except discord.HTTPException:
            await Helper.send_error(ctx, ctx.channel, "fail_prune_other")
        else:
            await Helper.send_success(ctx, ctx.channel, "success_prune", format_content=(len(messages),), delete_after=5.0)

    @mod.command(help="mod_kick_help", description="mod_kick_description")
    @commands.bot_has_permissions(kick_members=True)
    @commands.has_permissions    (kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason"):
        """Kicks a member"""

        await member.kick(reason=reason)

        file = discord.File("isartbot/media/kick.gif", filename="kick.gif")
        embed = await self.success_embed(ctx, 'success_kick', member.mention, ctx.author.mention, reason)
        embed.set_image(url="attachment://kick.gif")

        self.bot.logger.warning(f"{member.name} has been kicked by {ctx.author.name} for '{reason}'")
        await ctx.send(file=file, embed=embed)

    @mod.command(aliases=["banhammer", "derive_autoritaire", "begone"], help="mod_ban_help", description="mod_ban_description")
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions    (ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason"):
        """Bans a member"""

        await member.ban(reason=reason, delete_message_days=0)

        file_hammer = discord.File("isartbot/media/banhammer.gif", filename="banhammer.gif")
        file_salty  = discord.File("isartbot/media/saltyban.gif" , filename="saltyban.gif" )
        
        embed = await self.success_embed(ctx, 'success_ban', member.mention, ctx.author.mention, reason)
        embed.set_image(url="attachment://banhammer.gif")

        if (ctx.invoked_with == 'derive_autoritaire'):
            embed.set_image(url="attachment://saltyban.gif")
            await ctx.send(file=file_salty, embed=embed)
        else:
            embed.set_image(url="attachment://banhammer.gif")
            await ctx.send(file=file_hammer, embed=embed)

        self.bot.logger.warning(f"{member.name} has been banned by {ctx.author.name} for '{reason}'")

    """
    @mod.command(help="mod_as_help", description="mod_as_description", name = "as")
    @commands.check(is_moderator)
    async def _as(self, ctx, member : MemberConverter, *command_str : str):
        
        if (member is None):
            await Helper.send_error(ctx, ctx.channel, 'mod_as_success')
            return

        await Helper.send_success(ctx, ctx.channel, 'mod_as_success')

        prefix = self.bot.clean_prefix
        regex  = r"{0}(\w*)\s.*".format(prefix)
        matches = re.search(regex, command_str)

        embedFail = discord.Embed()
        embedFail.title = "Failed"
        embedFail.colour = discord.Color.red()

        if not matches:
            embedFail.description = 'There is no command to invoke.'
            await ctx.send(embed=embed)
            return

        command = self.bot.get_command(matches.group(1))
        if (not await command.can_run(ctx)):
            embedFail.description = "The checks for this command failed, "
                                    "maybe you don't have the required rights ?"
            await ctx.send(embed=embed)
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
                                "maybe you don't have the required rights?")
                return

        msg: discord.Message = await ctx.send(command_str)
        msg.author           = member
        await self.bot.process_commands(msg)

        return"""

    @mod.command(help="mod_for_help", description="mod_for_description", name='for')
    @commands.check(is_moderator)
    @commands.bot_has_permissions(manage_roles=True)
    async def _for(self, ctx, *args : Union[discord.Member, discord.Role, str]):
        """Removes or adds roles to members of the guild"""

        selectors, action, roles = [list(items) for _, items in groupby(args, key=lambda x: isinstance(x, str))]

        if len(action) != 1:
            await Helper.send_error(ctx, ctx.channel, 'mod_for_error')
            return

        action = action[0].lower()

        if action not in ['add', 'remove']:
            await Helper.send_error(ctx, ctx.channel, 'mod_for_error')
            return

        selected_members = set()

        # Adding members to the set
        for selection in selectors:
            if isinstance(selection, discord.Member):
                selected_members.add(selection)
                continue

            for member in selection.members:
                selected_members.add(member)

        # Creating add and remove strategies
        strategies = {'add' : self.for_add, 'remove' : self.for_remove}

        await strategies[action](selected_members, roles)

        await Helper.send_success(ctx, ctx.channel, 'mod_for_success', 
            format_content=(action, ' '.join([role.mention for role in roles]), ' '.join([selector.mention for selector in selectors])))

    # For strategies
    async def for_add(self, selected_members, roles):
        """ Add strategy, adds every roles passed to every of the selected members """
        for member in selected_members:
            for role in roles:
                await member.add_roles(role)

    async def for_remove(self, selected_members, roles):
        """ Remove strategy, removes every roles passed of every of the selected members """
        for member in selected_members:
            for role in roles:
                await member.remove_roles(role)

def setup(bot):
    bot.add_cog(ModerationExt(bot))
