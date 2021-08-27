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

import asyncio
import discord

from math                import ceil
from discord.ext         import commands
from isartbot.helper     import Helper
from isartbot.checks     import is_admin, is_verified
from isartbot.database   import SelfAssignableRole, Server
from isartbot.converters import BetterRoleConverter

class IamExt(commands.Cog):

    __slots__ = ("bot")

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """ Database role maintainance """

        server        = self.bot.database.session.query(Server).filter(Server.discord_id == role.guild.id).first()
        database_role = self.bot.database.session.query(SelfAssignableRole).\
            filter(SelfAssignableRole.discord_id == role.id, SelfAssignableRole.server == server).first()
        
        if (database_role == None):
            return

        self.bot.database.session.delete(database_role)
        self.bot.database.session.commit()

    @commands.command(pass_context=True, help="iam_help", description="iam_description")
    @commands.bot_has_permissions(send_messages=True, manage_roles=True)
    @commands.check(is_verified)
    async def iam(self, ctx, *, role: BetterRoleConverter):
        """ Adds a role to a user if possible """

        server        = self.bot.database.session.query(Server).filter(Server.discord_id == ctx.guild.id).first()
        database_role = self.bot.database.session.query(SelfAssignableRole).\
            filter(SelfAssignableRole.discord_id == role.id, SelfAssignableRole.server == server).first()

        if (database_role == None):
            await Helper.send_error(ctx, ctx.channel, 'sar_non_existant_role', format_content=(role.mention,))
            return

        try:
            await ctx.message.author.add_roles(role, reason="iam command")
            await Helper.send_success(ctx, ctx.channel, 'iam_success', format_content=(role.mention,))
        except:
            await Helper.send_error(ctx, ctx.channel, 'iam_failure', format_content=(role.mention,))


    @commands.command(pass_context=True, help="iamn_help", description="iamn_description")
    @commands.bot_has_permissions(send_messages=True, manage_roles=True)
    @commands.check(is_verified)
    async def iamn(self, ctx, *, role: BetterRoleConverter):
        """ Removes a role from the user """

        server        = self.bot.database.session.query(Server).filter(Server.discord_id == ctx.guild.id).first()
        database_role = self.bot.database.session.query(SelfAssignableRole).\
            filter(SelfAssignableRole.discord_id == role.id, SelfAssignableRole.server == server).first()

        if (database_role == None):
            await Helper.send_error(ctx, ctx.channel, 'sar_non_existant_role', format_content=(role.mention,))
            return

        try:
            await ctx.message.author.remove_roles(role, reason="iamn command")
            await Helper.send_success(ctx, ctx.channel, 'iamn_success', format_content=(role.mention,))
        except:
            await Helper.send_error(ctx, ctx.channel, 'iamn_failure', format_content=(role.mention,))

    @commands.group(pass_context=True, invoke_without_command=True)
    async def sar(self, ctx):
        """ Sar command group (sar stands for Self Assignable Role) """
        await ctx.send_help(ctx.command)

    @sar.command(aliases=["add"], help="sar_create_help", description="sar_create_description")
    @commands.check(is_admin)
    async def create(self, ctx, *, role: BetterRoleConverter):
        """ Creates a new self assignable role """

        # Looking for invalid roles
        if (role == ctx.guild.default_role):
            await Helper.send_error(ctx, ctx.channel, 'sar_invalid_role_error', format_content=(role.mention,))
            return

        # Looking for duplicates
        server        = self.bot.database.session.query(Server).filter(Server.discord_id == ctx.guild.id).first()
        database_role = self.bot.database.session.query(SelfAssignableRole).\
            filter(SelfAssignableRole.discord_id == role.id, SelfAssignableRole.server == server).first()

        if (database_role != None):
            await Helper.send_error(ctx, ctx.channel, 'sar_role_already_exists_error', format_content=(role.mention,))
            return

        # Creating the new role
        new_role = SelfAssignableRole(discord_id = role.id, server = server)

        self.bot.database.session.add(new_role)
        self.bot.database.session.commit()

        await Helper.send_success(ctx, ctx.channel, 'sar_role_created', format_content=(role.mention,))

    @sar.command(aliases=["remove"], help="sar_delete_help", description="sar_delete_description")
    @commands.check(is_admin)
    async def delete(self, ctx, *, role: BetterRoleConverter):
        """ Deletes a self assignable role """

        server        = self.bot.database.session.query(Server).filter(Server.discord_id == ctx.guild.id).first()
        database_role = self.bot.database.session.query(SelfAssignableRole).\
            filter(SelfAssignableRole.discord_id == role.id, SelfAssignableRole.server == server).first()

        if (database_role == None):
            await Helper.send_error(ctx, ctx.channel, 'sar_non_existant_role', format_content=(role.mention,))
            return

        self.bot.database.session.delete(database_role)
        self.bot.database.session.commit()

        await Helper.send_success(ctx, ctx.channel, 'sar_role_deleted', format_content=(role.mention,))

    @sar.command(help="sar_list_help", description="sar_list_description")
    async def list(self, ctx, page: int = 1):
        """ Lists all the self assignable roles for this guild """

        server = self.bot.database.session.query(Server).filter(Server.discord_id == ctx.guild.id).first()
        roles  = self.bot.database.session.query(SelfAssignableRole).\
            filter(SelfAssignableRole.server == server).all()

        max_lines   = int(self.bot.settings.get("iam", "list_max_lines"))
        total_pages = ceil(len(roles) / max_lines)

        # Clamping the current page
        page = min(max(1, page), total_pages)

        # Filling the embed content
        lines = []
        for index in range(max_lines * (page - 1), max_lines * page):
            try:
                role = ctx.guild.get_role(roles[index].discord_id)
                if (role != None):
                    lines.append(f"• {role.mention}")
            except IndexError:
                break

        embed = discord.Embed()
        embed.description = '\n'.join(lines)
        embed.title       = await ctx.bot.get_translation(ctx, 'sar_list_title')
        embed.color       = discord.Color.green()
        embed.set_footer(text = (await ctx.bot.get_translation(ctx, 'sar_list_footer')).format(page, total_pages))

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(IamExt(bot))