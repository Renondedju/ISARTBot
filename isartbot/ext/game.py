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

import discord
import asyncio

from math                import ceil
from discord.ext         import commands
from isartbot.helper     import Helper
from isartbot.checks     import is_moderator, is_verified
from isartbot.database   import Game, Server, SelfAssignableRole
from isartbot.converters import GameConverter
from isartbot.converters import MemberConverter

class GameExt (commands.Cog):

    def __init__(self, bot):

        # Starting the game assignation task
        self.bot  = bot
        self.task = bot.loop.create_task(self.run_game_task())

    def cog_unload(self):
        """Called when the game module is unloaded for any reason"""

        self.task.cancel()

    async def run_game_task(self):
        """Error handler for the game scan task"""
        
        try:
            await self.game_task()
        except asyncio.CancelledError: # This error is thrown when the extension is unloaded
            pass
        except Exception as e:
            await self.bot.on_error(e)

    async def game_task(self):
        """Scan for players and auto assigns game roles if possible"""

        scan_delay = int(self.bot.settings.get("game", "scan_delay"))
        
        # Main scan loop
        while (scan_delay != -1):

            # Fetching all required data from the database
            database_games = list(self.bot.database.session.query(Game).all())
            servers        = set([item.server for item in database_games])

            # Looping over every server that requires a scan
            for server in servers:
                guild = discord.utils.get(self.bot.guilds, id=server.discord_id)
                
                # We just got removed from a server while scanning, skipping it.
                # The next scan will be fine since all data related with this server
                # has already been removed from the database
                if (guild == None):
                    continue

                # Fetching server verified role (if any)
                verified_role = discord.utils.get(guild.roles, id = server.verified_role_id)
                server_games  = [game for game in database_games if game.server == server]

                # Looping over each members
                for member in guild.members:

                    # Checking for a verified role, this way unauthorized people don't get assigned roles
                    if (verified_role != None):
                        if (verified_role not in member.roles):
                            continue
                    
                    game_role = self.get_game_role_from_activity(member.activity, server_games, guild)
                    if (game_role == None or game_role in member.roles):
                        continue
                    
                    try:
                        await member.add_roles(game_role, reason="Automatic game scan")
                        self.bot.logger.info(f"Added the game {game_role.name} to {member} in guild named {guild.name}")
                    except discord.Forbidden: # If discord doesn't let us modify roles, then breaking to the next server
                        break
                    except:
                        pass

            # Waiting for the next scan
            await asyncio.sleep(scan_delay)

    def get_game_role_from_activity(self, activity: discord.Activity, server_games, guild: discord.Guild):
        """Returns a game role from an activity"""

        if not isinstance(activity, (discord.Game, discord.Activity)):
            return None

        game_name = activity.name.lower()

        # Looping over every available games to see if something is matching
        for game in server_games:
            if game_name == game.discord_name:
                return discord.utils.get(guild.roles, id=game.discord_role_id)
        
        return None

    @commands.group(invoke_without_command=True, pass_context=True,
        help="game_help", description="game_description")
    @commands.bot_has_permissions(manage_roles = True)
    async def game(self, ctx):
        await ctx.send_help(ctx.command)
    
    @game.command(help="game_add_help", description="game_add_description")
    @commands.check(is_verified)
    async def add(self, ctx, *, game: GameConverter):
        """ Adds a game to the user """

        if (game is None):
            await Helper.send_error(ctx, ctx.channel, 'game_invalid_argument')
            return

        game_role = discord.utils.get(ctx.guild.roles, id=game.discord_role_id)

        try:
            await ctx.message.author.add_roles(game_role, reason="game add command")
            await Helper.send_success(ctx, ctx.channel, 'game_add_success', format_content=(game_role.mention,))
        except:
            await Helper.send_error  (ctx, ctx.channel, 'game_add_failure', format_content=(game_role.mention,))

    @game.command(help="game_remove_help", description="game_remove_description")
    @commands.check(is_verified)
    async def remove(self, ctx, *, game: GameConverter):
        """ Adds a game to the user """

        if (game is None):
            await Helper.send_error(ctx, ctx.channel, 'game_invalid_argument')
            return

        game_role = discord.utils.get(ctx.guild.roles, id=game.discord_role_id)

        try:
            await ctx.message.author.remove_roles(game_role, reason="game remove command")
            await Helper.send_success(ctx, ctx.channel, 'game_remove_success', format_content=(game_role.mention,))
        except:
            await Helper.send_error  (ctx, ctx.channel, 'game_remove_failure', format_content=(game_role.mention,))

    @game.command(help="game_create_help", description="game_create_description")
    @commands.check(is_moderator)
    async def create(self, ctx, name, *, discord_name = ""):
        """Create a game"""

        if (discord_name == ""):
            discord_name = name

        game_check = await GameConverter().convert(ctx, name)

        if (game_check is not None):
            await Helper.send_error(ctx, ctx.channel, 'game_create_error_existing', format_content=(game_check.display_name,))
            return

        role_color = ctx.bot.settings.get("game", "role_color")
        game = await ctx.guild.create_role(
            name        = name,
            color       = await commands.ColourConverter().convert(ctx, role_color),
            mentionable = False)

        server = self.bot.database.session.query(Server).filter(Server.discord_id == ctx.guild.id).first()

        new_game = Game(
            discord_role_id = game.id,
            display_name    = name,
            discord_name    = discord_name.lower(),
            server          = server
        )

        sar = SelfAssignableRole(discord_id = game.id, server = server)

        self.bot.database.session.add(new_game)
        self.bot.database.session.add(sar)
        self.bot.database.session.commit()

        await Helper.send_success(ctx, ctx.channel, 'game_create_success', format_content=(game.mention,))

    @game.command(help="game_delete_help", description="game_delete_description")
    @commands.check(is_moderator)
    async def delete(self, ctx, *, game: GameConverter):
        """Deletes a game"""

        if (game is None):
            await Helper.send_error(ctx, ctx.channel, 'game_invalid_argument')
            return
            
        game_role = discord.utils.get(ctx.guild.roles, id=game.discord_role_id)

        confirmation = await Helper.ask_confirmation(ctx, ctx.channel, 'game_delete_confirmation_title',
            initial_content = "game_delete_confirmation_description" , initial_format = (game_role.mention,),
            success_content = "game_delete_success"                  , success_format = (game.display_name.title(),),
            failure_content = "game_delete_aborted")

        if (not confirmation):
            return

        self.bot.database.session.delete(game)
        self.bot.database.session.commit()

        await game_role.delete()

    @game.command(help="game_list_help", description="game_list_description")
    async def list(self, ctx, page: int = 1):
        """Lists the available games of the server"""

        # Fetching and computing all initial required data
        database_games = list(self.bot.database.session.query(Game).all())
        server_games   = [game for game in database_games if game.server.discord_id == ctx.guild.id]
        max_lines      = int(self.bot.settings.get("game", "list_max_lines"))
        total_pages    = ceil(len(server_games) / max_lines)

        # Clamping the current page
        page = min(max(1, page), total_pages)

        # Filling the embed content
        lines = []
        for index in range(max_lines * (page - 1), max_lines * page):
            try:
                lines.append(f"• {server_games[index].display_name}")
            except IndexError:
                break

        embed = discord.Embed()
        embed.description = '\n'.join(lines)
        embed.title       = await ctx.bot.get_translation(ctx, 'game_list_title')
        embed.color       = discord.Color.green()
        embed.set_footer(text = (await ctx.bot.get_translation(ctx, 'game_list_footer')).format(page, total_pages))

        await ctx.send(embed=embed)

    # Events
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """ Database role maintainance """

        server = self.bot.database.session.query(Server).filter(Server.discord_id == role.guild.id).first()
        game   = self.bot.database.session.query(Game).filter(Game.discord_role_id == role.id, Game.server == server).first()
        
        if (game == None):
            return

        self.bot.database.session.delete(game)
        self.bot.database.session.commit()

def setup(bot):
    bot.add_cog(GameExt(bot))