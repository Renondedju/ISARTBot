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
from discord.ext import commands

class Game_commands():

    def __init__(self, bot):

        #Private
        self.__bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    async def game(self, ctx):
        """ Creates a command group """

        if ctx.invoked_subcommand is None:
            await ctx.send("Game requiers a subcommand, if you need some help please"
                           " type ``{}help game``"
                           .format(self.__bot.settings.get("bot", "prefix")))

    @game.command(name='create', hidden=True)
    @commands.check(is_admin)
    async def _create(self, ctx, *, game_name: str):
        """ Creates a game if this game does not exists yet """

        game_name = game_name.lower().strip()

        #Checking if the game already exists
        if game_name in self.__bot.settings.get("games_roles", command="game"):
            await ctx.send("The game named {} already exists !".format(game_name))
            return

        #Retriving the game category
        game_category = None
        for cat in ctx.guild.categories:
            if str(cat.id) == str(ctx.bot.settings.get("category_id", command="game")):
                game_category = cat
                break

        #If the game category isn't found, raising an error
        if (game_category is None):
            raise commands.CommandError(message="No valid category id found. Aborting")

        #Otherwise creating it
        color = ctx.bot.settings.get("role_color", command="game")
        role = await ctx.guild.create_role(
            name        = game_name,
            colour      = discord.Colour(int(color, 16)),
            mentionable = True)

        ctx.bot.settings.write({"id" : role.id}, role.name, "games_roles", command="game")

        override = {role                   : discord.PermissionOverwrite(read_messages=True),
                    ctx.guild.default_role : discord.PermissionOverwrite(read_messages=False)}

        #Creating the text and vocal channels
        text  = await ctx.guild.create_text_channel (
            name       = game_name,
            category   = game_category,
            overwrites = override)

        vocal = await ctx.guild.create_voice_channel(
            name       = game_name,
            category   = game_category,
            overwrites = override)

        if (text is None or vocal is None):
            raise commands.CommandError(message="Failed to create the game channels")

        await ctx.send("Added the game {} to the list of avaliable games".format(role.mention))

        return

    @game.command(name='delete', hidden=True)
    @commands.check(is_admin)
    async def _delete(self, ctx, *, game_name: str):

        game_name = game_name.lower().strip()

        await ctx.send("TODO :)")

    @_delete.error
    @_create.error
    async def _error(self, ctx, error):
        """
            Catches errors of the create subcommand
        """

        if isinstance(error, commands.CheckFailure):
            await ctx.send("You need to be an admin to do that !")

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You missed an argument. Type __``{}help"
                            "game create``__ for some help"
                            .format(self.__bot.settings.get("bot", "prefix")))

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("I need some more permissions to do that sorry !")

        else:
            await ctx.bot.on_error(ctx, error)

        return

def setup(bot):
    bot.add_cog(Game_commands(bot))