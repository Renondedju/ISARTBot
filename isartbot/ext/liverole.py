# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018-2020 Renondedju

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

import asyncio
import discord
import logging

from discord.ext         import commands
from isartbot.database   import Server
from isartbot.checks     import is_moderator
from isartbot.converters import BetterRoleConverter

class LiveRoleExt(commands.Cog):

    def __init__(self, bot, *args, **kwargs):
        self.bot = bot

    # Command group
    @commands.group(pass_context=True, invoke_without_command=True, help="live_role_help", description="live_role_description")
    @commands.check(is_moderator)
    async def liverole(self, ctx):
        await ctx.send_help(ctx.command)

    # Sets the live role for the current server
    @liverole.command(help="live_role_set_help", description="live_role_set_description")
    @commands.check(is_moderator)
    async def set(self, ctx, role: BetterRoleConverter):
        
        embed = discord.Embed()

        # Checking if we have enough permissions in order to operate the starboard on the designated channel
        required_perms = discord.Permissions().none()
        required_perms.update(manage_roles=True)

        if (not required_perms.is_subset(ctx.message.channel.permissions_for(ctx.guild.me))):
            raise commands.BotMissingPermissions(["manage_roles"])

        self.bot.logger.info(f"Live role set to {role.name} ({role.id}) for server named {ctx.guild.name}")

        self.bot.database.session.query(Server).\
            filter(Server.discord_id == ctx.guild.id).\
            update({Server.live_role_id : role.id})

        self.bot.database.session.commit()

        embed.title       = await ctx.bot.get_translation(ctx, "success_title")
        embed.description = f"{await ctx.bot.get_translation(ctx, 'success_live_role_set')}: {role.mention}"
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    # Disables the live role for the current server
    @liverole.command(help="live_role_disable_help", description="live_role_disable_description")
    @commands.check(is_moderator)
    async def disable(self, ctx):
        
        self.bot.logger.info(f"Live role disabled for server named {ctx.guild.name}")

        self.bot.database.session.query(Server).\
            filter(Server.discord_id == ctx.guild.id).\
            update({Server.live_role_id : 0})

        self.bot.database.session.commit()

        embed = discord.Embed()
        embed.title       = await ctx.bot.get_translation(ctx, "success_title")
        embed.description = await ctx.bot.get_translation(ctx, "success_live_role_disable")
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    # Checks if the passed activities contains a stream
    def check_streaming_activity(self, activities):
        
        for activity in activities:
            if (isinstance(activity, discord.Streaming)):
                return True

        return False

    async def get_live_role_id(self, server: discord.Guild) -> int:
        """ Returns the setuped live role id for a given server """

        server = self.bot.database.session.query(Server).\
            filter(Server.discord_id == server.id).\
            first()

        if (server == None):
            return 0

        return server.live_role_id

    async def get_live_role(self, server: discord.Guild) -> discord.Role:

        role_id = await self.get_live_role_id(server)
        if (role_id != 0):
            return server.get_role(role_id)

        return None

    # Event listener in charge of role operations
    @commands.Cog.listener()
    async def on_member_update(self, before : discord.Member, after : discord.Member):
        
        # If the user activity changed
        if (not self.check_streaming_activity(before.activities) and self.check_streaming_activity(after.activities)):
            await self.on_stream_starts(after)

        elif (self.check_streaming_activity(before.activities) and not self.check_streaming_activity(after.activities)):
            await self.on_stream_stops(after)

    async def on_stream_starts(self, member : discord.Member):

        live_role = await self.get_live_role(member.guild)
        if (live_role == None):
            return

        self.bot.logger.info(f"{member} started streaming in guild named {member.guild.name} !")
        await member.add_roles(live_role)

    async def on_stream_stops(self, member : discord.Member):

        live_role = await self.get_live_role(member.guild)
        if (live_role == None):
            return

        self.bot.logger.info(f"{member} stopped streaming in guild named {member.guild.name} !")
        await member.remove_roles(live_role)

def setup(bot):
    bot.add_cog(LiveRoleExt(bot))
