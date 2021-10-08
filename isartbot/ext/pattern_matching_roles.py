# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018-2021 Renondedju

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

from math              import ceil
from typing            import Tuple
from discord.ext       import commands
from dataclasses       import dataclass
from isartbot.helper   import Helper
from isartbot.database import Server, RolePattern


@dataclass(frozen=True, init=True, repr=True)
class Pattern:
    """Represents a single pattern match"""

    role:  discord.Role = None
    regex: str          = ""

# TODO: Keep track of deleted roles
class PatternMatchingRolesExt(commands.Cog):
    """ 
        Checks for nickname changes, and attempts
        to assign a specific role based on the provided patterns
    """

    def __init__(self, bot: commands.Bot) -> None:
        """Default constructor"""

        super().__init__()

        self.bot = bot

    def get_guild_patterns(self, guild: discord.Guild) -> Tuple[Pattern]:
        """Returns all the role patterns for tha guild"""
        
        server      = self.bot.database.session.query(Server).filter(Server.discord_id == guild.id).first()
        db_patterns = server.role_patterns
        db_patterns.sort(key = lambda pattern: pattern.position)

        return [Pattern(guild.get_role(p.discord_role_id), p.regex) for p in db_patterns]

    @commands.group(invoke_without_command=True, pass_context=True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.has_permissions    (manage_roles = True)
    async def pattern(self, ctx):
        await ctx.send_help(ctx.command)

    @pattern.command(pass_context=True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.has_permissions    (manage_roles = True)
    async def create(self, ctx, role: discord.Role, regex_pattern: str) -> None:
        """Creates a role assignation pattern"""

        server      = self.bot.database.session.query(Server).filter(Server.discord_id == ctx.guild.id).first()
        new_pattern = RolePattern(
            discord_role_id = role.id,
            position        = len(server.role_patterns),
            regex           = regex_pattern,
            server          = server
        )

        self.bot.database.session.add(new_pattern)
        self.bot.database.session.commit()

        await Helper.send_success(ctx, ctx.channel, 'pattern_create_success', format_content=(role.mention, regex_pattern))

    @pattern.command(pass_context=True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.has_permissions    (manage_roles = True)
    async def delete(self, ctx, position: int) -> None:
        """Deletes a pattern"""

        pattern = ctx.bot.database.session.query(RolePattern).filter(RolePattern.position == position).first()
        
        if (pattern == None):
            return await Helper.send_error(ctx, ctx.channel, "pattern_delete_failure")
            
        # Asking for confirmation
        result = await Helper.ask_confirmation(ctx, ctx.channel, "pattern_delete_title",
            initial_content = "pattern_delete_content", initial_format = (pattern.regex, pattern.role.mention),
            success_content = "pattern_deleted"       , success_format = (pattern.regex, pattern.role.mention),
            failure_content = "pattern_delete_aborted")

        if (not result):
            return

        # Otherwise, deleting the diffusion
        self.bot.database.session.delete(pattern)
        self.bot.database.session.commit()
        

    @pattern.command(pass_context=True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.has_permissions    (manage_roles = True)
    async def reorder(self, ctx, id: int, new_position: int) -> None:
        pass

    @pattern.command(pass_context=True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.has_permissions    (manage_roles = True)
    async def list(self, ctx, page: int = 1) -> None:
        """Lists the current patterns of the guild"""

        patterns    = self.get_guild_patterns(ctx.guild)
        max_lines   = 10
        total_pages = ceil(len(patterns) / max_lines)

        # Clamping the current page
        page = min(max(1, page), total_pages)

        # Filling the embed content
        lines = []
        for index in range(max_lines * (page - 1), max_lines * page):
            try:
                lines.append(f"**{index}** • `{patterns[index].regex}` -> {patterns[index].role.mention}")
            except IndexError:
                break

        embed = discord.Embed()
        embed.description = '\n'.join(lines)
        embed.title       = "Role patterns list"
        embed.color       = discord.Color.green()
        embed.set_footer(text = f"Page {page} out of {total_pages}")

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """
            Called when a member is updated, if the member changed nickname, 
            the bot will attempt to match the new nick with a pattern and assign the corresponding role
        """

        # Ignoring the event if the nickname hasn't changed
        if before.nick == after.nick:
            return

        # Retreiving the list of patterns for this server
        patterns = self.get_guild_patterns(after.guild)
        roles    = [p.role for p in patterns]

        # Iterating over all the patterns for that guild
        for pattern in patterns:
            
            # Selecting the first match
            if re.match(str(pattern.regex), str(after.nick)):
                await after.remove_roles(*roles)
                await after.add_roles   (pattern.role, reason=f"New pattern matched a username change: {pattern.regex}")

                self.bot.logger.info(f"Member named {after.mention} changed nick to {after.nick} and got assigned the role {pattern.role.name} in guild named {after.guild.name}")

                return


def setup(bot):
    bot.add_cog(PatternMatchingRolesExt(bot))
