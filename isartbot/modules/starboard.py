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

from typing                  import Union, List
from isartbot.exceptions     import CogLoadingFailed
from discord.ext             import commands

class Starboard():
    """ Starboard class """

    def __init__(self, bot):

        self.bot = bot

        # Fetching parameters
        self.stars      = self.bot.settings.get('stars'     , command = 'starboard')
        self.min_stars  = self.bot.settings.get('min_stars' , command = 'starboard')
        self.channel_id = self.bot.settings.get('channel_id', command = 'starboard')

        self.star_channel = self.bot.get_channel(self.channel_id)

        # Sorting the stars (and conveting the keys to integers)
        self.stars = {int(k):v for k,v in self.stars.items()}
        self.stars = dict(sorted(self.stars.items()))

        # If something failed
        if self.stars is None or self.min_stars is None or self.bot.guild.id is None:
            raise CogLoadingFailed('Failed to load one or more settings')

        if self.star_channel is None:
            raise CogLoadingFailed('There is no starboard channel !')

    def check_enabled(self):
        """ Checks if the starboard is enabled or not """

        return self.bot.settings.get("enabled", command='starboard')

    def check_star(self, reaction : Union[discord.Reaction, List[discord.Reaction]]) -> bool:
        """ Checks if there is a star in the reactions """

        #If the reaction is a discord.Reaction
        if isinstance(reaction, discord.Reaction):
            # If the message of the reaction isn't in the main guild
            # ignoring the reaction
            if reaction.message.guild.id != self.bot.guild.id:
                return False

            return reaction.emoji == '⭐'
        
        if isinstance(reaction, list):
            # For each reaction in the list
            for react in reaction:

                # If the message of the reaction isn't in the main guild
                # ignoring the reaction
                if reaction.message.guild.id != self.bot.guild.id:
                    return False

                if react.emoji == '⭐':
                    return True
        
        return False

    def count_stars(self, message : discord.Message) -> int:
        """ Counts how many stars there is on the message """

        # For each reaction in the message, if the reaction is a star
        # returning the count of reactions
        for reaction in message.reactions:
            if self.check_star(reaction):
                return reaction.count

        return 0

    def create_embed(self, message : discord.Message) -> discord.Embed:
        """ Creates an embed for a starboard message """

        # Generating the embed
        embed = discord.Embed()
        embed.color = discord.Color.gold()

        if message is None:
            return embed

        # Seting the author
        url = "https://discordapp.com/channels/{0.guild.id}/{0.channel.id}/{0.id}".format(message)
        embed.set_author(name=message.author.display_name,
                         url=url,
                         icon_url=message.author.avatar_url)

        # Seting the embed content
        embed.description = message.content

        # Iterating every attachment and adding it the the embed
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

        # Seting the footer 
        embed.set_footer(text="Id : {0.id}".format(message))

        return embed

    async def get_starboard_message(self, message : discord.Message) -> discord.Message:
        """ Retruns a starboard message if there is one corresponding
            Returns none otherwise
        """

        # Generating the footer text we are looking for
        text = 'id : {0.id}'.format(message)

        # Looking into the history of the starboard channel and looking for an 
        # embed message that has the same footer as the variable 'text'
        async for history_message in self.star_channel.history(limit=20):
            for embed in history_message.embeds:
                if isinstance(embed.footer.text, str) and embed.footer.text.lower() == text:
                    return history_message

        return None

    async def star_message(self, message : discord.Message):
        """ Creates an entry on the starboard """

        # Creating the embed and content of the message 
        embed   = self.create_embed(message)
        content = ':star: **x1** {0.mention}'.format(message.channel)

        # Sending the message and a log
        await self.star_channel.send(content, embed=embed)
        self.bot.logs.print('Starred message with id : {0.id}'.format(message))

        return

    def get_star_emoji(self, count : int) -> str:
        """ Returns the emoji to use of the count of stars """

        # Default emoji is :star:
        emoji = ":star:"

        # Since the self.stars dict has been sorted, we can check
        # for each star icon if the count variable is high enough to use it.
        for number, text in self.stars.items():
            print(number, text)
            if int(count) >= int(number):
                emoji = text
            else:
                return emoji

        return emoji

    async def edit_star(self, message: discord.Message, count : int):
        """ Edits a stared message on the starboard to set a fixed count of stars on it """

        # Fetching the starboard message
        starboard_message = await self.get_starboard_message(message)
        if starboard_message is None:
            return

        # Generating the new content of the message
        emoji = self.get_star_emoji(count)
        text = '{0} **x{1}** {2.mention}'.format(emoji, str(count), message.channel)

        # Editing the starboard message 
        await starboard_message.edit(content=text)
        self.bot.logs.print('Stared message with id : {0.id}, has now {1} stars'
            .format(message, count))

        return

    async def unstar_message(self, message : discord.Message):
        """ Removes a stared message from the starboard """

        # Fetching the starboard message
        starboard_message = await self.get_starboard_message(message)

        # And deleting it if it is a valid message
        if starboard_message is not None:
            self.bot.logs.print('Deleting message from starboard with id : {0.id}'.format(message))
            await starboard_message.delete()

        return

    # --- Events --- 
    async def on_reaction_add(self, reaction : discord.Reaction, user: discord.User):

        # Checking if the starboard is enabled and if the reaction is a star
        if not self.check_star(reaction) or not self.check_enabled():
            return

        # Fetching the starboard message and the reaction count
        starboard_message = await self.get_starboard_message(reaction.message)
        count = self.count_stars(reaction.message)

        # If there is no starboard message and there is enough stars: staring the message
        if count >= self.min_stars and starboard_message is None:
            await self.star_message(reaction.message)

        # Editing the message to update the stars count
        await self.edit_star(reaction.message, count)

    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        
        # Checking if the starboard is enabled and if the reaction is a star
        if not self.check_star(reaction) or not self.check_enabled():
            return

        # Counting the number of reactions
        count = self.count_stars(reaction.message)
        
        # If there is not enough stars anymore, unstaring the message
        if (count < self.min_stars):
            await self.unstar_message(reaction.message)
            return

        # Editing the message to update the star count
        await self.edit_star(reaction.message, count)

    async def on_reaction_clear(self, message: discord.Message, reactions: List[discord.Reaction]):
        
        # Checking if the starboard is enabled and if there is a star in the reactions
        if not self.check_star(reactions) or not self.check_enabled():
            return

        #If there is: unstaring the message
        await self.unstar_message(message)


def setup(bot):
    bot.add_cog(Starboard(bot))