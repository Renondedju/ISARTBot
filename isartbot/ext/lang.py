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

import asyncio
import discord
import logging

from isartbot.models import ServerPreferences
from discord.ext     import commands
from isartbot.checks import is_moderator, is_super_admin

class LangExt(commands.Cog):

    @commands.group(pass_context=True, invoke_without_command=True)
    async def lang(self, ctx):

        if ctx.invoked_subcommand is None:
            await ctx.send(await ctx.bot.get_translation(ctx, 'invalid_command_usage'))

    @lang.command()
    @commands.check(is_super_admin)
    async def reload(self, ctx):
        """ Reloads all the langs from the files """

        await ctx.bot.load_languages()

        embed = discord.Embed()

        embed.title       = await ctx.bot.get_translation(ctx, 'success_title')
        embed.description = await ctx.bot.get_translation(ctx, 'language_reload_success')
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    @lang.command()
    async def list(self, ctx):
        """ Lists all the available languages for this server """

        embed = discord.Embed()

        embed.title       = await ctx.bot.get_translation(ctx, 'lang_list_title')
        embed.description = '\n'.join(['• ' + lang for (lang, file_name) in ctx.bot.settings.items("languages")])
        embed.colour      = discord.Color.green()
        embed.set_footer(text = await ctx.bot.get_translation(ctx, 'lang_list_footer'))

        await ctx.send(embed=embed)

    @lang.command()
    @commands.check(is_moderator)
    async def set(self, ctx, lang: str):
        """ Sets a language for the current server """

        embed = discord.Embed()

        if (lang not in ctx.bot.langs):
            embed.title       = await ctx.bot.get_translation(ctx, 'failure_title')
            embed.description = await ctx.bot.get_translation(ctx, 'lang_not_available')
            embed.colour      = discord.Color.red()
        else:
            await self.set_language(ctx, lang)

            embed.title       = await ctx.bot.get_translation(ctx, 'success_title')
            embed.description = await ctx.bot.get_translation(ctx, 'lang_set')
            embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    async def set_language(self, ctx, lang):
        await ctx.bot.database.connection.execute(
            ServerPreferences.table.update().\
                where (ServerPreferences.table.c.discord_id == ctx.guild.id).\
                values(lang=lang)
        )

def setup(bot):
    bot.add_cog(LangExt())
