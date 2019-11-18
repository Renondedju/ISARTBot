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

import emoji
import asyncio
import discord

class Helper():

    @staticmethod
    async def send_success(ctx, channel: discord.TextChannel, content: str, format_content: tuple = (), **kwargs):
        """ Sends a success message to the targetted discord text channel """

        translations = await ctx.bot.get_translations(ctx, ["success_title", content])
        embed = discord.Embed(
            title       = translations["success_title"],
            description = translations[content].format(*format_content),
            color       = discord.Color.green()
        )
        
        return await channel.send(embed=embed, **kwargs)

    @staticmethod
    async def send_error(ctx, channel: discord.TextChannel, content: str, format_content: tuple = (), **kwargs):
        """ Sends an error message to the targetted discord text channel """
        
        translations = await ctx.bot.get_translations(ctx, ["failure_title", content])
        embed = discord.Embed(
            title       = translations["failure_title"],
            description = translations[content].format(*format_content),
            color       = discord.Color.red()
        )

        return await channel.send(embed=embed, **kwargs)

    @staticmethod
    async def ask_confirmation(ctx, channel: discord.TextChannel,
        title: str, initial_content: str       , success_content: str       , failure_content: str,
                    initial_format : tuple = (), success_format : tuple = (), failure_format: tuple = ()) -> bool:
        
        value, _, _ = await Helper.ask_confirmation_and_get_message(ctx, channel, title,
            initial_content, success_content, failure_content,
            initial_format , success_format , failure_format)

        return value

    @staticmethod
    async def ask_confirmation_and_get_message(ctx, channel: discord.TextChannel,
        title: str, initial_content: str       , success_content: str       , failure_content: str,
                    initial_format : tuple = (), success_format : tuple = (), failure_format: tuple = ()):

        translations = await ctx.bot.get_translations(ctx, [initial_content, title, failure_content, "confirmation_footer", success_content])

        embed = discord.Embed(
            title       = translations[title],
            description = translations[initial_content].format(*initial_format)
        )

        embed.set_footer(text = translations["confirmation_footer"])

        message = await channel.send(embed = embed)
        
        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == emoji.emojize(":thumbs_up:")

        if (channel.permissions_for(ctx.guild.me).add_reactions):
            await message.add_reaction(emoji.emojize(":thumbs_up:"))

        try:
            await ctx.bot.wait_for('reaction_add', timeout = 10.0, check = check)

        except asyncio.TimeoutError:

            embed.description = translations[failure_content].format(*failure_format)
            embed.color       = discord.Color.red()
            embed.set_footer()
            
            await message.edit(embed = embed)

            return False, message, embed

        embed.description = translations[success_content].format(*success_format)
        embed.color       = discord.Color.green()
        embed.set_footer()

        await message.edit(embed = embed)

        return True, message, embed