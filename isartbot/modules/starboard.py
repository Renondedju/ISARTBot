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

import re
import discord

from isartbot.exceptions     import CogLoadingFailed
from discord.ext             import commands

class Starboard():
    """ Starboard class """

    def __init__(self, bot):

        self.bot = bot

        #Displayed stars 
        self.stars     = self.bot.settings.get('stars'    , command = 'starboard')
        self.min_stars = self.bot.settings.get('min_stars', command = 'starboard')

        self.guild_id     = self.bot.settings.get('bot', 'server_id')
        self.channel_id   = self.bot.settings.get('channel_id', command = 'starboard')
        self.star_channel = self.bot.get_channel(self.channel_id)

        if self.stars is None or self.min_stars is None or self.guild_id is None:
            raise CogLoadingFailed('Failed to load one or more settings')

        if self.star_channel is None:
            raise CogLoadingFailed('There is no starboard channel !')

    def check_enabled(self):
        """ Checks if the starboard is enabled or not """

        return self.bot.settings.get("enabled", command='starboard')

    def check_star(self, reaction):
        """ Checks if there is a star in the reactions """

        if isinstance(reaction, discord.Reaction):
            if reaction.message.guild.id != self.guild_id:
                return False

            return reaction.emoji == '⭐'
        
        if isinstance(reaction, list):
            for react in reaction:
                if reaction.message.guild.id != self.guild_id:
                    return False

                if react.emoji == '⭐':
                    return True
        
        return False

    def count_stars(self, message : discord.Message) -> int:
        """ Counts how many stars there is on the message """

        for reaction in message.reactions:
            if reaction.emoji == '⭐':
                return reaction.count

        return 0

    def create_embed(self, message : discord.Message) -> discord.Embed:
        """ Creates an embed for a starboard message """
        
        embed = discord.Embed()
        embed.color = discord.Color.gold()

        if message is None:
            return embed

        url = "https://discordapp.com/channels/{0.guild.id}/{0.channel.id}/{0.id}".format(message)
        embed.set_author(name=message.author.display_name,
                         url=url,
                         icon_url=message.author.avatar_url)

        embed.description = message.content
        has_image = False

        if (len(message.attachments) is not 0):
            value = []

            for attachment in message.attachments:
                if attachment.height != 0 and has_image is False:
                    embed.set_image(url=attachment.proxy_url)
                    has_image = True
                else:
                    value.append("[{0.filename}]({0.url})".format(attachment))

            if len(value) is not 0:
                embed.add_field(name='Attachments', value='\n'.join(value), inline=False)

        embed.set_footer(text="Id : {0.id}".format(message))

        return embed

    async def get_starboard_message(self, message):
        """ Retruns a starboard message if there is one corresponding
            Returns none otherwise
        """
        text = 'id : {0.id}'.format(message)

        async for history_message in self.star_channel.history(limit=20):
            for embed in history_message.embeds:
                if isinstance(embed.footer.text, str) and embed.footer.text.lower() == text:
                    return history_message

    async def star_message(self, message):
        """ Creates an entry on the starboard """

        embed   = self.create_embed(message)
        content = ':star: **x1** {0.mention}'.format(message.channel)

        await self.star_channel.send(content, embed=embed)
        self.bot.logs.print('Starred message with id : {0.id}'.format(message))

    async def edit_star(self, message, count):
        """ Edits a stared message on the starboard to set a fixed count of stars on it """

        starboard_message = await self.get_starboard_message(message)

        if starboard_message is None:
            return

        emoji = ":star:"
        for number, text in self.stars.items():
            if count >= int(number):
                emoji = text
            else:
                break

        text = '{0} **x{1}** {2.mention}'.format(emoji, str(count), message.channel)

        await starboard_message.edit(content=text)
        self.bot.logs.print('Stared message with id : {0.id}, has now {1} stars'
            .format(message, count))

    async def unstar_message(self, message):
        """ Removes a stared message from the starboard """

        starboard_message = await self.get_starboard_message(message)

        if starboard_message is not None:
            self.bot.logs.print('Deleting message from starboard with id : {0.id}'.format(message))
            await starboard_message.delete()

    #Events 
    async def on_reaction_add(self, reaction, user):

        if not self.check_star(reaction) or not self.check_enabled():
            return

        starboard_message = await self.get_starboard_message(reaction.message)
        count = self.count_stars(reaction.message)

        if count >= self.min_stars and starboard_message is None:
            await self.star_message(reaction.message)

        await self.edit_star(reaction.message, count)

    async def on_reaction_remove(self, reaction, user):
        
        if not self.check_star(reaction) or not self.check_enabled():
            return

        count = self.count_stars(reaction.message)
        
        if (count < self.min_stars):
            await self.unstar_message(reaction.message)
            return

        await self.edit_star(reaction.message, count)

    async def on_reaction_clear(self, message, reactions):
        
        if not self.check_star(reactions) or not self.check_enabled():
            return

        await self.unstar_message(message)

def setup(bot):
    bot.add_cog(Starboard(bot))