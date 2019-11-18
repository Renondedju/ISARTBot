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
import asyncio

from discord.ext          import commands
from discord.ext.commands import RoleConverter

from isartbot.converters  import upper_clean
from isartbot.converters  import ClassConverter
from isartbot.converters  import MemberConverter
from isartbot.checks      import is_moderator
from isartbot.helper      import Helper

class ClassExt (commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def get_class(self, ctx, class_name: upper_clean):
        """Returns the class role if existing"""

        return discord.utils.get(ctx.guild.roles, name=class_name)

    @commands.group(pass_context=True, invoke_without_command=True, 
        help="class_help", description="class_description", name="class")
    @commands.check(is_moderator)
    @commands.bot_has_permissions(manage_roles = True)
    async def _class(self, ctx):
        """Class modification command"""
        await ctx.send_help(ctx.command)

    @_class.command(help="class_create_help", description="class_create_description")
    @commands.check(is_moderator)
    @commands.bot_has_permissions(manage_roles = True)
    async def create(self, ctx, name: upper_clean):
        """Creates a class"""

        user_check = await MemberConverter().convert(ctx, name)
        role_check = await ClassConverter ().convert(ctx, name)

        if (role_check is not None):
            await Helper.send_error(ctx, ctx.channel, "class_create_error", (role_check.mention,))
            return

        if (user_check is not None):
            await Helper.send_error(ctx, ctx.channel, "class_create_name_error", (user_check.mention,))
            return

        role = self.get_class(ctx, name)

        if (role is not None):
            await Helper.send_error(ctx, ctx.channel, "class_create_error", (role.mention,))
            return

        role_color = ctx.bot.settings.get("class", "role_color")

        role = await ctx.guild.create_role(
            name        = name,
            color       = discord.Color(int(role_color, 16)),
            mentionable = True)

        await Helper.send_success(ctx, ctx.channel, "class_create_success", (role.mention,))

    @_class.command(help="class_delete_help", description="class_delete_description")
    @commands.check(is_moderator)
    @commands.bot_has_permissions(manage_roles = True)
    async def delete(self, ctx, name: ClassConverter):
        """Deletes a class"""

        if (name is None):
            await Helper.send_error(ctx, ctx.channel, "class_invalid_argument")
            return

        await Helper.ask_confirmation(ctx, ctx.channel, "class_delete_confirmation_title", 
            initial_content="class_delete_confirmation_description", initial_format=(name.mention,),
            success_content="class_delete_success"                 , success_format=(name.mention,),
            failure_content="class_delete_aborted")

        await name.delete()

        return

    @_class.command(help="class_rename_help", description="class_rename_description")
    @commands.check(is_moderator)
    @commands.bot_has_permissions(manage_roles = True)
    async def rename(self, ctx, old_name: ClassConverter, new_name: upper_clean):
        """Renames a class"""

        if (old_name is None):
            await Helper.send_error(ctx, ctx.channel, "class_invalid_argument")
            return

        class_check  = await ClassConverter ().convert(ctx, new_name)
        member_check = await MemberConverter().convert(ctx, new_name)

        if (class_check is not None or member_check is not None):
            await Helper.send_error(ctx, ctx.channel, "class_rename_error")
            return

        new_role = self.get_class(ctx, new_name)

        if (new_role is not None):
            await Helper.send_error(ctx, ctx.channel, "class_rename_error")
            return

        name = old_name.name

        await old_name.edit(name=new_name)
        await Helper.send_success(ctx, ctx.channel, "class_rename_success", (name, old_name.mention,))

def setup(bot):
    bot.add_cog(ClassExt(bot))
