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

from discord.ext         import commands
from isartbot.helper     import Helper
from isartbot.checks     import is_moderator
from isartbot.database   import Game
from isartbot.converters import GameConverter
from isartbot.converters import MemberConverter

class GameExt (commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    @commands.group(pass_context=True, help="game_help", description="game_description")
    @commands.check(is_moderator)
    @commands.bot_has_permissions(manage_roles = True)
    async def game(self, ctx):
        pass
    
    @game.command(help="game_create_help", description="game_create_description")
    @commands.check(is_moderator)
    @commands.bot_has_permissions(manage_roles = True)
    async def create(self, ctx, name, discord_name = ""):
        """Create a game"""

        game_check = await GameConverter().convert(ctx, name)

        if (game_check is not None):
            await Helper.send_error(ctx, ctx.channel, 'game_create_error_existing', format_content=(game_check.display_name,))
            return

        role_color = ctx.bot.settings.get("game", "role_color")
        game = await ctx.guild.create_role(
            name        = name,
            color       = discord.Color(int(role_color, 16)),
            mentionable = True)

        new_game = Game(discord_role_id = game.id, display_name = game.name.lower(), discord_name = discord_name, server_id = ctx.guild.id)

        self.bot.database.session.add(new_game)
        self.bot.database.session.commit()

        await Helper.send_success(ctx, ctx.channel, 'game_create_success', format_content=(game.mention,))

    @game.command(help="game_delete_help", description="game_delete_description")
    @commands.check(is_moderator)
    @commands.bot_has_permissions(manage_roles = True)
    async def delete(self, ctx, name: GameConverter):
        """Deletes a game"""

        if (name is None):
            await Helper.send_error(ctx, ctx.channel, 'game_invalid_argument')
            return
            
        game = await commands.RoleConverter().convert(ctx, name.display_name.title())

        confirmation = await Helper.ask_confirmation(ctx, ctx.channel, 'game_delete_confirmation_title',
            initial_content = "game_delete_confirmation_description" , initial_format = (game.mention,),
            success_content = "game_delete_success"                  , success_format = (name.display_name.title(),),
            failure_content = "game_delete_aborted")

        if (not confirmation):
            return

        self.bot.database.session.delete(name)
        self.bot.database.session.commit()

        await game.delete()

def setup(bot):
    bot.add_cog(GameExt(bot))