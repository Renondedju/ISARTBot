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

class Starboard(commands.Cog):
    """ Starboard related commands and tasks """

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

        # Creating the starboard message buffer.
        # Since the 'on_reaction_x' events are only trigerred on cashed messages
        # there is no need to look into the history of the star channel.
        # So to optimize things we are gonna store those messages to avoid doing 
        # requests to the discord API.
        self.star_buffer = set()
        self.bot.loop.create_task(self.init_starboard_buffer())

        # If something failed
        if self.stars is None or self.min_stars is None or self.bot.guild.id is None:
            raise CogLoadingFailed('Failed to load one or more settings')

        if self.star_channel is None:
            raise CogLoadingFailed('There is no starboard channel !')

    def check_enabled(self):
        """ Checks if the starboard is enabled or not """

        return self.bot.settings.get("enabled", command='starboard')

    def get_message_url(self, original_message: discord.Message) -> str:
        """ Returns the url of the message """

        if original_message is None:
            return ""

        return 'https://discordapp.com/channels/{0.guild.id}/{0.channel.id}/{0.id}'.format(original_message)

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

    def is_starboard_message(self, message: discord.Message):
        """ Checks if the message is a starboard message """

        if message is None:
            return False

        # If the message is in the starboard channel
        if message.channel == self.star_channel:

            # And if the message has embeds
            if len(message.embeds) > 0:

                # If the author url of the first embed of the message 
                # starts with 'https://discordapp.com/channels/', then it's 
                # a starboard message
                return str(message.embeds[0].author.url).startswith('https://discordapp.com/channels/')

        return False

    def get_star_emoji(self, count : int) -> str:
        """ Returns the emoji to use of the count of stars """

        # Default emoji is :star:
        emoji = ":star:"

        # Since the self.stars dict has been sorted, we can check
        # for each star icon if the count variable is high enough to use it.
        for number, text in self.stars.items():
            if int(count) >= int(number):
                emoji = text
            else:
                return emoji

        return emoji

    def create_embed(self, message : discord.Message) -> discord.Embed:
        """ Creates an embed for a starboard message """

        # Generating the embed
        embed = discord.Embed()
        embed.color = discord.Color.gold()

        if message is None:
            return embed

        # Seting the author
        url = self.get_message_url(message)
        embed.set_author(name=message.author.display_name,
                         url=url,
                         icon_url=message.author.avatar_url)

        # Seting the embed content
        if message.content:
            embed.description = message.content
        
        elif len(message.embeds) > 0:
            embed.description = message.embeds[0].description
            embed.title       = message.embeds[0].title

            if message.embeds[0].image.url != discord.Embed.Empty:
                embed.set_image(url=message.embeds[0].image.url)
        
            return embed

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

        return embed

    async def init_starboard_buffer(self):
        """ Inits the starboard message buffer """

        # This function is called once per module init. 
        # This function avoids a bug where reloading the starboard module without
        # rebooting the bot would create duplicated starboard messages if a reaction event
        # is fired on a cached message (by the discord.py lib).

        async for message in self.star_channel.history(limit=20):
            self.star_buffer.add(message)

        return

    async def count_stars(self, original_message : discord.Message, 
                                starboard_message: discord.Message) -> int:
        """ Counts how many stars there is on the message """

        unique_users = set()

        # Counts every star on the original message
        for reaction in original_message.reactions:
            if self.check_star(reaction):
                unique_users = set(await reaction.users().flatten())
                break

        # If there is still no starboard message, stoping here
        if starboard_message is None:
            return len(unique_users)

        # Otherwise, returning stars_count plus the number of star reactions under the
        # starboard message
        for reaction in starboard_message.reactions:
            if self.check_star(reaction):
                unique_users |= set(await reaction.users().flatten())
                break
                
        return len(unique_users)

    async def get_original_message(self, starboard_message: discord.Message) -> discord.Message:
        """ Gets the original message from a starboard message """

        if starboard_message is None or len(starboard_message.embeds) == 0:
            return None

        author_url = starboard_message.embeds[0].author.url
    
        r = r"https:\/\/discordapp\.com\/channels\/\d*\/(\d*)\/(\d*)"
        match = re.search(r, author_url)

        if not match:
            return None

        channel_id = match.group(1)
        message_id = match.group(2)

        channel = self.bot.guild.get_channel(int(channel_id))
        if channel is None:
            return None
        
        return await channel.get_message(message_id)

    async def get_starboard_message(self, original_message : discord.Message) -> discord.Message:
        """ Retruns a starboard message from the original message if there is one corresponding
            Returns none otherwise
        """

        if original_message is None:
            return None

        # Checking if the message itself is a starboard message
        if self.is_starboard_message(original_message):
            return original_message

        # Generating author url we are looking for
        url = self.get_message_url(original_message)

        # Looking into the history of the starboard channel and looking for an 
        # embed message that has the same author url than the variable 'url'
        for history_message in self.star_buffer:
            for embed in history_message.embeds:
                if embed.author.url == url:
                    return history_message

        return None

    async def star_message(self, message : discord.Message):
        """ Creates an entry on the starboard """

        # Creating the embed and content of the message 
        embed   = self.create_embed(message)
        emoji   = self.get_star_emoji(self.min_stars)
        content = '{2} **x{1}** {0.mention}'.format(message.channel, self.min_stars, emoji)

        # Sending the message and a log
        message = await self.star_channel.send(content, embed=embed)
        self.star_buffer.add(message)

        # If the buffer contains more than 30 starboard messages : discarding the older one
        if len(self.star_buffer) > 30:
            self.star_buffer.pop()

        self.bot.logs.print('Starred message with id : {0.id}'.format(message))

        return

    async def edit_star(self, count: int, starboard_message: discord.Message):
        """ Edits a stared message on the starboard to set a fixed count of stars on it """

        # Generating the new content of the message
        emoji = self.get_star_emoji(count)
        text = starboard_message.content

        while not text.startswith('<#'):
            text = text[1:]

        text = '{0} **x{1}** {2}'.format(emoji, str(count), text)

        # Editing the starboard message 
        return await starboard_message.edit(content=text)

    async def unstar_message(self, message : discord.Message):
        """ Removes a stared message from the starboard """

        # Fetching the starboard message
        starboard_message = await self.get_starboard_message(message)

        # And deleting it if it is a valid message
        if starboard_message is not None:
            self.bot.logs.print('Deleting message from starboard with id : {0.id}'.format(message))
            await starboard_message.delete()

            self.star_buffer.discard(starboard_message)
            
        return

    # --- Events --- 
    async def on_reaction_add(self, reaction, user):

        # Checking if the starboard is enabled and if the reaction is a star
        if not self.check_enabled() or not self.check_star(reaction):
            return

        # Fetching the starboard message and the original message
        original_message  = await self.get_original_message (reaction.message)
        starboard_message = await self.get_starboard_message(reaction.message)

        if original_message == None:
            original_message = reaction.message

        count = await self.count_stars(original_message, starboard_message)

        # If there is no starboard message and if there is enough stars and
        # if the message isn't a starboard message : staring the message
        if count >= self.min_stars and starboard_message is None and not self.is_starboard_message(reaction.message):
            return await self.star_message(reaction.message)

        # Editing the message to update the stars count
        return await self.edit_star(count, starboard_message)

    async def on_reaction_remove(self, reaction, user):
        
        # Checking if the starboard is enabled and if the reaction is a star
        if not self.check_star(reaction) or not self.check_enabled():
            return

        # Fetching the starboard message and the original message
        original_message  = await self.get_original_message (reaction.message) 
        starboard_message = await self.get_starboard_message(reaction.message)

        if original_message == None:
            original_message = reaction.message
        
        count = await self.count_stars(original_message, starboard_message)
        
        # If there is not enough stars anymore, and if this message isn't a starboard message :
        # unstaring the message
        if count < self.min_stars:
            return await self.unstar_message(original_message)

        # Editing the message to update the star count
        return await self.edit_star(count, starboard_message)

    async def on_reaction_clear(self, message, reactions):
        
        # Checking if the starboard is enabled and if there is a star in the reactions
        if not self.check_star(reactions) or not self.check_enabled():
            return

        # Fetching the starboard message and the original message
        original_message  = await self.get_original_message (message) 
        starboard_message = await self.get_starboard_message(message)

        if original_message == None:
            original_message = message

        if message.id == starboard_message.id:
            count = await self.count_stars(original_message, starboard_message)
            return await self.edit_star(count, starboard_message)
            
        #If there is: unstaring the message
        return await self.unstar_message(message)


def setup(bot):
    bot.add_cog(Starboard(bot))