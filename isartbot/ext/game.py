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
from isartbot.converters import upper_clean
from isartbot.converters import ClassConverter
from isartbot.converters import MemberConverter
from isartbot.checks     import is_moderator

class GameExt (commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    async def error_embed(self, ctx, description: str, *args):
        """Create an error embed"""

        return discord.Embed(
            title       = await ctx.bot.get_translation(ctx, "failure_title"),
            description = (await ctx.bot.get_translation(ctx, description)).format(*args),
            color       = discord.Color.red())

    async def success_embed(self, ctx, description: str, *args):
        """Create a success embed"""

        return discord.Embed(
            title       = await ctx.bot.get_translation(ctx, 'success_title'),
            description = (await ctx.bot.get_translation(ctx, description)).format(*args),
            color       = discord.Color.green())

    @commands.group(pass_context=True, help="game_help", 
                    description="game_description", name = "game")
    @commands.check(is_moderator)
    @commands.bot_has_permissions(manage_roles = True)
    async def _game(self, ctx):

        pass
    
    @_game.command(help="game_create_help", description="game_create_description")
    @commands.check(is_moderator)
    @commands.bot_has_permissions(manage_roles = True)
    async def create(self, ctx, name: upper_clean):
        """Create a game"""

        user_check = await MemberConverter().convert(ctx, name)
        role_check = await ClassConverter().convert(ctx, name)

        if (role_check is not None):
            await ctx.send(embed= await self.error_embed(ctx, 'game_create_error_existing', role_check.mention))
            return

        if (user_check is not None):
            await ctx.send(embed= await self.error_embed(ctx, 'game_create_error_invalid', user_check.mention))
            return

        role_color = ctx.bot.settings.get("game", "role_color")

        game = await ctx.guild.create_role(
            name        = name,
            color       = discord.Color(int(role_color, 16)),
            mentionable = True)

        await ctx.send(embed = await self.success_embed(ctx, 'game_create_success', game.mention))

    @_game.command(help="game_delete_help", description="game_delete_description")
    @commands.check(is_moderator)
    @commands.bot_has_permissions(manage_roles = True)
    async def delete(self, ctx, name: ClassConverter):
        """Deletes a game"""

        if (name is None):
            await ctx.send(embed= await self.error_embed(ctx, 'game_invalid_argument', None))
            return

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '👍'

        embed=discord.Embed(
            description = (await ctx.bot.get_translation(ctx, 'game_delete_confirmation_description')).format(name.mention),
            title       = await ctx.bot.get_translation(ctx, 'game_delete_confirmation_title'))
            
        embed.set_footer(text = await ctx.bot.get_translation(ctx, 'game_delete_footer'))

        message = await ctx.send(embed=embed)
        
        await message.add_reaction('👍')

        try:
            await ctx.bot.wait_for('reaction_add', timeout=5.0, check=check)

        except asyncio.TimeoutError:
            embed.description = await ctx.bot.get_translation(ctx, 'game_delete_aborted')
            embed.color = discord.Color.red()
            embed.set_footer()
            
            await message.clear_reactions()

            await message.edit(embed=embed)
            return

        old_name = name.name

        await name.delete()

        await message.clear_reactions()

        await message.edit(embed= await self.success_embed(ctx, 'game_delete_success', old_name))
        return

def setup(bot):
    bot.add_cog(GameExt(bot))