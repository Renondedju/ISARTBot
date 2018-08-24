# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018 Renondedju

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

from isartbot.bot_decorators import is_dev, is_admin
from isartbot.settings       import Settings
from isartbot.logs           import Logs
from discord.ext             import commands
from math                    import ceil

class Game_commands():

    def __init__(self, bot):

        #Private
        self.bot = bot
        self.task = self.bot.loop.create_task(self.check_for_games())

    def __unload(self):
        self.task.cancel()

    async def check_for_games(self):
        """ Scan games and auto assign """

        guild_id = self.bot.settings.get('bot', 'server_id')
        delay    = self.bot.settings.get('auto_assign_refresh_delay', command = "game")
        guild    = self.bot.get_guild(guild_id)
        isartian = discord.utils.get(guild.roles, id=self.bot.settings.get('bot', 'isartian_role_id'))

        if (isartian is None):
            self.bot.logs.print("Isartian role not found !")
            self.bot.logs.print("Aborting game task, restart it by reloading the game module.")
            return

        while (delay != -1):
            await asyncio.sleep(delay)

            if not self.bot.settings.get('enabled', command = "game"):
                pass
            
            for member in guild.members:

                if isartian not in member.roles:
                    pass

                if isinstance(member.activity, (discord.Game, discord.Activity)):
                    game = member.activity.name.lower()
                    role = discord.utils.get(guild.roles,
                        id = self.bot.settings.get("games_roles", game, "id", command="game"))

                    try:
                        if role not in member.roles:
                            await member.add_roles(role)
                            self.bot.logs.print(
                                f'Added the game {role.name} to {member.name}#{member.discriminator}')
                    except:
                        pass

        self.bot.logs.print(f'Auto assign game loop finished !')

    @commands.group(pass_context=True, invoke_without_command=True)
    async def game(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.bot.send_fail(ctx,
                "Game subcommand not recognized.\nIf you need some help please"
                " type ``{}help game``"
                .format(self.bot.settings.get("bot", "prefix")),
                "Game")

    def get_game_category(self, ctx):
        """ Retriving the game category """

        for cat in ctx.guild.categories:
            if str(cat.id) == str(ctx.bot.settings.get("category_id", command="game")):
                return cat

        return None 

        #Create command
    @game.command(name='create', hidden=True)
    @commands.check(is_admin)
    async def _create(self, ctx, *, game_name: str):
        """ Creates a game role if this game does not exists yet (admin only) """

        game_name = game_name.lower().strip()

        #Checking if the game already exists
        if game_name in self.bot.settings.get("games_roles", command="game"):
            await ctx.bot.send_fail(ctx, 
                "The game named {} already exists !".format(game_name),
                "Create game")
            return

        game_category = self.get_game_category(ctx)

        #If the game category isn't found, raising an error
        if (game_category is None):
            raise commands.CommandError(message="No valid category id found. Aborting")

        #Otherwise creating it
        color = ctx.bot.settings.get("role_color", command="game")
        role = await ctx.guild.create_role(
            name        = game_name,
            colour      = discord.Colour(int(color, 16)),
            mentionable = True)

        override = {role                   : discord.PermissionOverwrite(read_messages=True),
                    ctx.guild.default_role : discord.PermissionOverwrite(read_messages=False)}

        #Creating the text and vocal channels
        text  = await ctx.guild.create_text_channel (
            name       = game_name,
            category   = game_category,
            overwrites = override)

        if (text is None):
            raise commands.CommandError(message="Failed to create the game channels")

        ctx.bot.settings.write({"id"    : role.id,
                                "vocal" : [],
                                "text"  : [text.id]},
            role.name, "games_roles", command="game")

        await ctx.bot.send_success(ctx,
            "Added the game {} to the list of avaliable games".format(role.mention),
            "Create game")

        return

        #Delete command
    
    @game.command(name='delete', hidden=True)
    @commands.check(is_admin)
    async def _delete(self, ctx, *, game_name: str):
        """ Deletes a game role (Admin only) """
        game_name = game_name.lower().strip()

        #Checking if the game exists
        if game_name not in self.bot.settings.get("games_roles", command="game"):
            await ctx.bot.send_fail(ctx, "The game named {} does not exists !".format(game_name))
            return

        game_category = self.get_game_category(ctx)

        role = discord.utils.get(ctx.guild.roles,
            id=ctx.bot.settings.get("games_roles", game_name, "id", command="game"))

        if (role is None):
            raise commands.CommandError(message="No valid role found. Aborting")

        #If the game category isn't found, raising an error
        if (game_category is None):
            raise commands.CommandError(message="No valid category id found. Aborting")

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '👍'

        embed = discord.Embed()

        embed.description = "Are you sure you want to delete the game {} ?".format(role.mention)
        embed.title       = "Delete game ?"
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

        reason = "This channel is deleted due to the game role @{} being deleted".format(game_name)

        try:
            for id in ctx.bot.settings.get("games_roles", game_name, "text", command="game"):
                text = ctx.bot.get_channel(id)
                if (text != None):
                    await text.delete(reason=reason)

            for id in ctx.bot.settings.get("games_roles", game_name, "vocal", command="game"):
                vocal = ctx.bot.get_channel(id)
                if (vocal != None):
                    await vocal.delete(reason=reason)

            await role.delete()

        except:
            raise commands.CommandError(message="Failed to delete a role or channel !")
        
        ctx.bot.settings.delete(role.name, "games_roles", command="game")


        embed.description += "\n\nSuccessfully deleted the game {} !".format(game_name)
        embed.color = discord.Color.green()
        
        await message.edit(embed=embed)

    @_delete.error
    @_create.error
    async def _error(self, ctx, error):
        """
            Catches errors of the create and delete subcommands
        """

        if isinstance(error, commands.CheckFailure):
            await ctx.bot.send_fail(ctx,
                "You need to be an admin to do that !"
                ,"Command failed")

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.bot.send_fail(ctx,
                "You missed an argument. Type __``{}help"
                " game``__ for some help"
                .format(self.bot.settings.get("bot", "prefix")),
                "Command failed")

        elif isinstance(error, commands.MissingPermissions):
            await ctx.bot.send_fail(ctx,
                "I need some more permissions to do that sorry !"
                ,"Command failed")

        else:
            await ctx.bot.on_error(ctx, error)

        return

        #Add command
    
    @game.command(name='add')
    async def _add(self, ctx, *, game_name: str):
        """ Adds a game role to the user """
        
        game_name = game_name.lower().strip()

        role = discord.utils.get(ctx.guild.roles,
            id=ctx.bot.settings.get("games_roles", game_name, "id", command="game"))

        if role is None:
            return await ctx.bot.send_fail(ctx,
                "No corresponding game role found"
                "\nUse ``{}game list`` to have the list of all the games avaliable for now"
                .format(self.bot.settings.get("bot", "prefix"))
                ,"Game")

        text = ctx.bot.get_channel(ctx.bot.settings.get(
            "games_roles", game_name, "text", command="game")[0])

        if role in ctx.message.author.roles:
            return await ctx.bot.send_fail(ctx,
                "You already have this game role !"
                "\nIf you are lost here is your channel {}".format(text.mention),
                "Game")

        await ctx.message.author.add_roles(role)

        await text.send("{0.mention} just joined the {1}'s world ! Gl & Hf !"
            .format(ctx.author, game_name))

        return await ctx.bot.send_success(ctx, 
            "Role added ! Have fun in {} !".format(text.mention),
            "Game")

    @_add.error
    async def _add_error(self, ctx, error):
        """ Catches the game add command errors """

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.bot.send_fail(ctx,
                "You missed an argument. Type __``{}help"
                " game add``__ for some help"
                .format(self.bot.settings.get("bot", "prefix")),
                "Command failed")

        elif isinstance(error, commands.MissingPermissions):
            await ctx.bot.send_fail(ctx,
                "I need some more permissions to do that sorry !"
                ,"Command failed")

        else:
            await ctx.bot.on_error(ctx, error)

        #Remove command
    @game.command(name='remove')
    async def _remove(self, ctx, *, game_name: str):
        """ Removes a game role to the user """
        
        game_name = game_name.lower().strip()

        role = discord.utils.get(ctx.guild.roles,
            id=ctx.bot.settings.get("games_roles", game_name, "id", command="game"))

        if role is None:
            return await ctx.bot.send_fail(ctx,
                "No corresponding game role found"
                "\nUse ``{}game list`` to have the list of all the games avaliable for now"
                .format(self.bot.settings.get("bot", "prefix"))
                ,"Game")

        if role in ctx.message.author.roles:
            await ctx.message.author.remove_roles(role)

            return await ctx.bot.send_success(ctx, 
                "Game role removed !",
                "Game")
        
        return await ctx.bot.send_fail(ctx, 
            "Sorry but I can't remove you a role that you don't have",
            "Game")

    @_remove.error
    async def _remove_error(self, ctx, error):
        """ Catches the game remove command errors """

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.bot.send_fail(ctx,
                "You missed an argument. Type __``{}help"
                " game add``__ for some help"
                .format(self.bot.settings.get("bot", "prefix")),
                "Command failed")

        elif isinstance(error, commands.MissingPermissions):
            await ctx.bot.send_fail(ctx,
                "I need some more permissions to do that sorry !"
                ,"Command failed")

        else:
            await ctx.bot.on_error(ctx, error)

    #List command
    @game.command(name='list')
    async def _list(self, ctx, page = 1):
        """ lists the games avaliable """

        games     = list(ctx.bot.settings.get("games_roles", command="game").keys())
        max_lines = ctx.bot.settings.get(  "list_max_lines", command="game")
        max_pages = ceil(len(games) / max_lines)

        page = max(1, page)
        page = min(page, max_pages)

        lines = []
        for index in range(max_lines * (page - 1), max_lines * page):
            try:
                lines.append(games[index])
            except IndexError:
                break

        text  = "```\n{}```".format('\n'.join(lines))

        embed = discord.Embed()

        embed.description = text
        embed.title       = "Game list"
        embed.color       = discord.Color.green()
        embed.set_footer(text = f"Page {page} out of {max_pages}")

        await ctx.send(embed=embed)

    @_list.error
    async def _list_error(self, ctx, error):
        """ Catches the game list command errors """

        if isinstance(error, commands.MissingPermissions):
            await ctx.bot.send_fail(ctx,
                "I need some more permissions to do that sorry !"
                ,"Command failed")

        else:
            await ctx.bot.on_error(ctx, error)

def setup(bot):
    bot.add_cog(Game_commands(bot))