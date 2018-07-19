# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2018 Renondedju

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
sys.path.append("./Lib/discord.py")
sys.path.append("../")

from bot_decorators import is_dev, is_admin
import logs
import discord
import asyncio
import settings
from math import ceil

from discord.ext import commands

class Class_commands():

    def __init__(self, bot):

        #Private
        self.__bot = bot

    def get_class(self, ctx, class_name : str):
        """ Checks if a class exists or not """

        category = None
        role     = None

        for cat in ctx.guild.categories:
            if cat.name == class_name:
                category = cat

        for r in ctx.guild.roles:
            if r.name == class_name:
                role = r

        return category, role

    @commands.group(pass_context=True, invoke_without_command=True, name='class')
    async def _class(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.bot.send_fail(ctx,
                "Class subcommand not recognized.\nIf you need some help please"
                " type ``{}help class``".format(self.__bot.settings.get("bot", "prefix")))

    @_class.command(name='create', hidden=True)
    @commands.check(is_admin)
    async def _create(self, ctx, name):
        """ Creates a class """

        name = name.upper().strip()

        cat, role = self.get_class(ctx, name)

        if cat is not None or role is not None:
            await ctx.bot.send_fail(ctx, "This class already exists !", "Error")
            return

        color = ctx.bot.settings.get("role_color", command="class")
        role = await ctx.guild.create_role(
            name        = name,
            colour      = discord.Colour(int(color, 16)),
            mentionable = True)

        overwrites = {role                   : discord.PermissionOverwrite(read_messages=True),
                      ctx.guild.default_role : discord.PermissionOverwrite(read_messages=False)}

        category = await ctx.guild.create_category_channel(name, overwrites=overwrites)

        for vocal_name in ctx.bot.settings.get("default_vocals", command="class"):
            await ctx.guild.create_voice_channel(
                name       = vocal_name,
                category   = category,
                overwrites = overwrites)

        for text_name in ctx.bot.settings.get("default_texts", command="class"):
            await ctx.guild.create_text_channel(
                name       = text_name,
                category   = category,
                overwrites = overwrites)

        await ctx.bot.send_success(ctx,
            f"Successfully added {role.mention} the the available classes",
            "Class creation")

    @_class.command(name='delete', hidden=True)
    @commands.check(is_admin)
    async def _delete(self, ctx, *, name):
        """ Deletes a class """

        name = name.upper().strip()

        category, role = self.get_class(ctx, name)

        if category is None:
            await ctx.bot.send_fail(ctx, "This class does not exists !", "Delete class ?")
            return

        if role is None:
            await ctx.bot.send_fail(ctx, f"There is no role named {name}.", "Delete class ?")
            return

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '👍'

        embed = discord.Embed()
        embed.description = f"Are you sure you want to delete the class {role.mention} ?"
        embed.title       = "Delete class ?"
        embed.set_footer(text="React with 👍 if you want to continue")

        message = await ctx.send(embed=embed)

        await message.add_reaction('👍')

        try:
            await ctx.bot.wait_for('reaction_add', timeout=5.0, check=check)

        except asyncio.TimeoutError:
            embed.description += "\n\nAborted deletion."
            embed.color = discord.Color.red()
            
            await message.edit(embed=embed)
            return

        try:
            for channel in category.channels:
                await channel.delete()

            await role.delete()
            await category.delete()

        except:
            embed.description += f"\n\nFailed to delete a role or channel !"
            embed.color = discord.Color.red()

            await message.edit(embed=embed)
            return

        embed.description += f"\n\nSuccessfully deleted the class {name} !"
        embed.color = discord.Color.green()
        
        await message.edit(embed=embed)

    @_create.error
    @_delete.error
    async def _error(self, ctx, error):
        """ Handles class command errors """

        if isinstance(error, commands.CheckFailure):
            await ctx.bot.send_fail(ctx,
                "You need to be an admin to do that !"
                ,"Command failed")

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.bot.send_fail(ctx,
                "You missed an argument. Type __``{}help"
                " class``__ for some help"
                .format(self.__bot.settings.get("bot", "prefix")),
                "Command failed")

        elif isinstance(error, commands.MissingPermissions):
            await ctx.bot.send_fail(ctx,
                "I need some more permissions to do that sorry !"
                ,"Command failed")

        else:
            await ctx.bot.on_error(ctx, error)

        return

    @_class.command(name='rename', hidden=True)
    @commands.check(is_admin)
    async def _rename(self, ctx, original_name, new_name):
        """ Renames a class """

        original_name = original_name.upper().strip()
        new_name      = new_name     .upper().strip()

        old_category, old_role = self.get_class(ctx, original_name)
        new_category, new_role = self.get_class(ctx, new_name)

        if (new_category is not None) or (new_role is not None) or (old_category is None) or (old_role is None):
            raise commands.CommandError(message="One of the roles is missing or already exists")
    
        await old_role    .edit(name=new_name)
        await old_category.edit(name=new_name)

        await ctx.bot.send_success(ctx,
            f"The class @{original_name} has successfully renamed to {old_role.mention}",
            "Rename class")

def setup(bot):
    bot.add_cog(Class_commands(bot))