# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018-2019 Renondedju

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

from discord.ext import commands

from isartbot.checks.moderator          import is_moderator
from isartbot.models.server_preferences import ServerPreferences

class StarboardExt(commands.Cog):
    """ Starboard related commands and tasks """

    __slots__ = ("bot")

    def __init__(self, bot, *args, **kwargs):

        self.bot = bot

    # Commands

    @commands.group(pass_context=True)
    @commands.bot_has_permissions(send_messages=True)
    @commands.check(is_moderator)
    async def starboard(self, ctx):
        pass

    @starboard.command()
    async def set(self, ctx, channel: discord.TextChannel):
        """ Sets the current starboard channel, if none was set before, this command also enables the starboard """

        embed = discord.Embed()

        # Checking if we have enough permissions in order to operate the starboard on the designated channel
        required_perms = discord.Permissions().none()
        required_perms.update(send_messages=True, manage_messages=True, read_messages=True)

        if (not required_perms.is_subset(channel.permissions_for(ctx.guild.me))):
            embed.title       = await ctx.bot.get_translation(ctx, "failure_title")
            embed.description = f"{await ctx.bot.get_translation(ctx, 'missing_bot_perms_error')}: [send_messages, manage_messages, read_messages]"
            embed.colour      = discord.Color.red()

            await ctx.send(embed=embed)
            return
        
        self.bot.logger.info(f"Starboard set to channel {channel.id} for server named {ctx.guild.name}")

        await self.bot.database.connection.execute(
            ServerPreferences.table.update().\
                where (ServerPreferences.table.c.discord_id == ctx.guild.id).\
                values(starboard_id=channel.id)
        )

        embed.title       = await ctx.bot.get_translation(ctx, "success_title")
        embed.description = f"{await ctx.bot.get_translation(ctx, 'success_starboard_set')}: {channel.mention}"
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    @starboard.command()
    async def disable(self, ctx):
        """ Disables the starboard for the current server, use "!starboard set <channel name>" to re enable it """

        self.bot.logger.info(f"Starboard disabled for server named {ctx.guild.name}")
        
        await self.bot.database.connection.execute(
            ServerPreferences.table.update().\
                where (ServerPreferences.table.c.discord_id == ctx.guild.id).\
                values(starboard_id=0)
            )
                    
        embed = discord.Embed()
        embed.title       = await ctx.bot.get_translation(ctx, "success_title")
        embed.description = await ctx.bot.get_translation(ctx, "success_starboard_unset")
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    # Events

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        self.bot.logger.info(f"Added reaction: {reaction.emoji}, {user.name}")

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        self.bot.logger.info(f"Removed reaction: {reaction.emoji}, {user.name}")

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        self.bot.logger.info(f"Cleared reactions: {reactions}")

def setup(bot):
    bot.add_cog(StarboardExt(bot))
