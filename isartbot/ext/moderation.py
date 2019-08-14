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

from discord.ext                        import commands

from isartbot.checks.moderator          import is_moderator
from isartbot.models.server_preferences import ServerPreferences

class ModerationExt(commands.Cog):
    """Helps with moderation"""

    def __init__(self, bot):

        #Private
        self.bot = bot

    @commands.group(pass_context=True)
    @commands.check(is_moderator)
    async def mod(self, ctx):
        pass


    #Prune command
    @mod.command(help="mod_prune_help", description="mod_prune_description")
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def prune(self, ctx, number: int, member: discord.Member = None):
        """Deletes a certain amount of the latest messages in this text channel"""

        embed = discord.Embed()
        embed.title = "Sucess"
        embed.colour = discord.Color.green()

        messages = []
        if (member is None):
            embed.description = f"Last {number} messages has been removed"
            messages = await ctx.channel.history(limit=number + 1).flatten()
        else:
            async for message in ctx.channel.history(limit=number + 1):
                if (message.author == member):
                     messages.append(message)
            messages.append(ctx.message)
            embed.description = f"Last {number} messages from {member.mention} has been removed"

        await ctx.channel.delete_messages(set(messages))

        await ctx.send(embed=embed)

    #Kick command
    @mod.command(help="mod_kick_help", description="mod_kick_description")
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="Because"):
        """Kicks a member"""

        embed = discord.Embed()

        await member.kick(reason=reason)

        string = f"{member.mention} was kicked by {ctx.author.mention} for reason: {reason}"

        embed.title = "Success"
        embed.description = string
        embed.colour = discord.Color.green()

        self.bot.logger.info(string)

        await ctx.send(embed=embed)

    #Ban command
    @mod.command(aliases=["banhammer", "derive_autoritaire", "restriction_de_la_liberte_d_expression"], help="mod_ban_help", description="mod_ban_description")
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="Nothing special"):
        """Bans a member"""
        await member.ban(reason=reason, delete_message_days=0)

        embed = discord.Embed()

        string = f"{member} was banned by {ctx.author} for reason: {reason}"

        embed.title = "Success"
        embed.description = string
        embed.colour = discord.Color.green()

        self.bot.logger.info(string)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(ModerationExt(bot))
