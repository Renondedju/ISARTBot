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
from isartbot.checks     import is_moderator, is_admin
from isartbot.database   import Server
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

    @mod.command(help="mod_log_set_help", description="mod_log_set_description")
    @commands.check(is_admin)
    async def log_set(self, ctx, channel: discord.TextChannel):
        """ Sets the current mod log channel, if none was set before, this command also enables the mod logging """

        embed = discord.Embed()

        # Checking if we have enough permissions in order to operate the starboard on the designated channel
        required_perms = discord.Permissions().none()
        required_perms.update(send_messages=True)

        if (not required_perms.is_subset(channel.permissions_for(ctx.guild.me))):
            raise commands.BotMissingPermissions(["send_messages"])

        self.bot.logger.info(f"Mod log channel set to {channel.id} for server named {ctx.guild.name}")

        self.bot.database.session.query(Server).\
            filter(Server.discord_id == ctx.guild.id).\
            update({Server.modlog_channel_id : channel.id})

        self.bot.database.session.commit()

        embed.title       =    await ctx.bot.get_translation(ctx, "success_title")
        embed.description = f"{await ctx.bot.get_translation(ctx, 'success_mod_log_set')}: {channel.mention}"
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    @mod.command(help="mod_log_unset_help", description="mod_log_unset_description")
    @commands.check(is_admin)
    async def log_unset(self, ctx):
        """ Disables the mod log for the current server, use "!mod log_set <channel name>" to re enable it """

        self.bot.logger.info(f"Mod log disabled for server named {ctx.guild.name}")

        self.bot.database.session.query(Server).\
            filter(Server.discord_id == ctx.guild.id).\
            update({Server.modlog_channel_id : 0})

        self.bot.database.session.commit()

        embed = discord.Embed()
        embed.title       = await ctx.bot.get_translation(ctx, "success_title")
        embed.description = await ctx.bot.get_translation(ctx, "success_mod_log_unset")
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

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

    @mod.command(help="mod_for_help", description="mod_for_description", name='for')
    @commands.check(is_moderator)
    @commands.bot_has_permissions(manage_roles=True)
    async def _for(self, ctx, *args : Union[discord.Member, discord.Role, str]):
        """Removes or adds roles to members of the guild"""

        commands  		 = [list(items) for _, items in groupby(args, key=lambda x: isinstance(x, str))]
        strategies       = {'add' : self.for_add, 'remove' : self.for_remove, 'with' : self.for_with}
        selected_members = set()

        # Adding members to the set
        for selection in commands[0]:
            if isinstance(selection, discord.Member):
                selected_members.add(selection)
                continue

            for member in selection.members:
                selected_members.add(member)

        value = 1
        while value < len(commands):
            action = commands[value][0]
            selected_members = await strategies[action](selected_members, commands[value + 1])
            value += 2

        await ctx.send("Done")

    # For strategies
    async def for_with(self, selected_members, roles) -> set():
        new_set = set()

        for member in selected_members:
            if all(item in member.roles for item in roles):
                new_set.add(member)

        return new_set

    async def for_add(self, selected_members, roles) -> set():
        """ Add strategy, adds every roles passed to every of the selected members """
        for member in selected_members:
            for role in roles:
                await member.add_roles(role)

        return selected_members

    async def for_remove(self, selected_members, roles) -> set():
        """ Remove strategy, removes every roles passed of every of the selected members """
        for member in selected_members:
            for role in roles:
                await member.remove_roles(role)

        return selected_members

    # Events
    @commands.Cog.listener()
    async def on_message_delete(self, message):

        # Checking if mod log is enabled
        server = self.bot.database.session.query(Server).filter(Server.discord_id == message.guild.id).first()
        if (server.modlog_channel_id == 0):
            return
        
        embed = discord.Embed()

        embed.description = message.content
        embed.title       = "Message deleted"
        embed.color       = discord.Color.red()

        # Adding attachments
        if message.attachments:
            file = message.attachments[0]
            if file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                embed.set_image(url=file.proxy_url)
            else:
                embed.add_field(name='Attachment', value=f'[{file.filename}]({file.proxy_url})', inline=False)

        embed.add_field (name="channel", value=message.channel.mention, inline=False)
        embed.set_footer(text=f"{message.author.name}#{message.author.discriminator}", icon_url=message.author.avatar_url)

        await self.bot.get_channel(server.modlog_channel_id).send(embed=embed)

def setup(bot):
    bot.add_cog(ModerationExt(bot))
