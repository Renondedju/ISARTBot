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

import re
import emoji
import discord
import asyncio

from discord.ext import commands

from isartbot.helper   import Helper
from isartbot.checks   import is_moderator, denied
from isartbot.database import Server

class StarboardExt(commands.Cog):
    """ Starboard related commands and tasks """

    __slots__ = ("bot", "stars", "minimum_stars", "locks")

    def __init__(self, bot, *args, **kwargs):

        self.bot   = bot
        self.locks = {}

        # Sorting the stars (and conveting the keys to integers)
        self.stars = {int(k):v for k,v in self.bot.settings.items("starboard_icons")}
        self.stars = dict(sorted(self.stars.items()))

    # Commands
    @commands.group(pass_context=True, invoke_without_command=True,
        help="starboard_help", description="starboard_description")
    @commands.check(is_moderator)
    async def starboard(self, ctx):
        await ctx.send_help(ctx.command)

    @starboard.command(help="starboard_set_help", description="starboard_set_description")
    @commands.check(is_moderator)
    async def set(self, ctx, channel: discord.TextChannel):
        """ Sets the current starboard channel, if none was set before, this command also enables the starboard """

        embed = discord.Embed()

        # Checking if we have enough permissions in order to operate the starboard on the designated channel
        required_perms = discord.Permissions().none()
        required_perms.update(send_messages=True, manage_messages=True, read_messages=True)

        if (not required_perms.is_subset(channel.permissions_for(ctx.guild.me))):
            raise commands.BotMissingPermissions(["send_messages", "manage_messages", "read_messages"])

        self.bot.logger.info(f"Starboard set to channel {channel.id} for server named {ctx.guild.name}")

        self.bot.database.session.query(Server).\
            filter(Server.discord_id == ctx.guild.id).\
            update({Server.starboard_channel_id : channel.id})

        self.bot.database.session.commit()

        embed.title       = await ctx.bot.get_translation(ctx, "success_title")
        embed.description = f"{await ctx.bot.get_translation(ctx, 'success_starboard_set')}: {channel.mention}"
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    @starboard.command(help="starboard_disable_help", description="starboard_disable_description")
    @commands.check(is_moderator)
    async def disable(self, ctx):
        """ Disables the starboard for the current server, use "!starboard set <channel name>" to re enable it """

        self.bot.logger.info(f"Starboard disabled for server named {ctx.guild.name}")

        self.bot.database.session.query(Server).\
            filter(Server.discord_id == ctx.guild.id).\
            update({Server.starboard_channel_id : 0})

        self.bot.database.session.commit()

        embed = discord.Embed()
        embed.title       = await ctx.bot.get_translation(ctx, "success_title")
        embed.description = await ctx.bot.get_translation(ctx, "success_starboard_unset")
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    @starboard.command(help="starboard_minimum_help", description="starboard_minimum_description")
    @commands.check(is_moderator)
    async def minimum(self, ctx, star_count: int):
        """ Sets the minimum star count for the current server's starboard """

        if (star_count < 1 or star_count > 100):
            await Helper.send_error(ctx, ctx.channel, "starboard_minimum_error")
            return

        self.bot.database.session.query(Server).\
            filter(Server.discord_id == ctx.guild.id).\
            update({Server.starboard_minimum : star_count})

        self.bot.database.session.commit()

        self.bot.logger.info(f"Starboard's star count changed to {star_count} for server named {ctx.guild.name}")

        await Helper.send_success(ctx, ctx.channel, "starboard_minimum_success", format_content=(star_count,))

    # Methods
    def get_emoji_message(self, message: discord.Message, star_count : int):
        """ Returns the starboarded version of a message """

        emoji   = self.get_star_emoji(star_count)
        content = f'{emoji} **{star_count}**'

        embed = discord.Embed(description=message.content)

        # Adding image or attachments
        if message.embeds:
            data = message.embeds[0]
            if data.type == 'image':
                embed.set_image(url=data.url)

        if message.attachments:
            file = message.attachments[0]
            if file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                embed.set_image(url=file.url)
            else:
                embed.add_field(name='Attachment', value=f'[{file.filename}]({file.url})', inline=False)

        embed.colour    = discord.Color.gold()
        embed.set_author(name     = message.author.display_name,
                         url      = message.jump_url,
                         icon_url = message.author.avatar_url_as(format='png'))

        embed.add_field(name="Original", value=f"[Jump!]({message.jump_url})", inline=False)

        return content, embed

    def get_star_emoji(self, star_count : int) -> str:
        """ Returns the emoji to use of the count of stars """

        # Default emoji is :star:
        emoji = ":star:"

        # Since the self.stars dict has been sorted, we can check
        # for each star icon if the star_count variable is high enough to use it.
        for (reaction_count, emoji_name) in self.stars.items():
            if star_count >= reaction_count:
                emoji = emoji_name
            else:
                return emoji

        return emoji

    def is_control_emoji(self, reaction_emoji) -> bool:
        """ Checks if the passed emoji is the control emoji """

        # Retreiving the emoji code ex.: ":star:"
        if isinstance(reaction_emoji, str):
            reaction_emoji = emoji.demojize(reaction_emoji)
        else:
            reaction_emoji = reaction_emoji.name

        return reaction_emoji == self.bot.settings.get('starboard', 'control_emoji')

    async def is_starboard_message(self, message: discord.Message) -> bool:
        """ Checks if the message is a starboard message """

        if message is None:
            return False

        # If the message is in a starboard channel
        # And if the author is the bot
        # and if the message has embeds
        if (    message.author.id   ==       self.bot.user.id
            and message.channel.id  == await self.get_starboard_channel_id(message.guild)
            and len(message.embeds) >  0):

            # If the author url of the first embed of the message
            # starts with 'https://discordapp.com/channels/' or 'https://discord.com/channels/', then it's
            # a starboard message
            link = str(message.embeds[0].author.url)
            return link.startswith('https://discordapp.com/channels/') or link.startswith('https://discord.com/channels/')

        return False

    async def get_starboard_channel_id(self, server: discord.Guild) -> int:
        """ Returns the setuped starboard channel id for a given server """

        servers = self.bot.database.session.query(Server).\
            filter(Server.discord_id == server.id).\
            all()

        # Something is wrong, either the server is not registered in the database,
        # either there is more than one server with this id, which shouldn't be possible
        if (len(servers) != 1):
            self.bot.logger.warning("Starboard configuration ambiguity ! Please check the database integrity.")
            return 0

        server = servers[0]

        return server.starboard_channel_id

    async def get_starboard_channel(self, server: discord.Guild) -> discord.TextChannel:
        """ Returns the starboard channel of a given guild, or None if there is none"""

        channel_id = await self.get_starboard_channel_id(server)

        if (channel_id != 0):
            return server.get_channel(channel_id)

        return None

    async def get_original_message(self, starboard_message: discord.Message) -> discord.Message:
        """ Gets the original message from a starboard message """

        if starboard_message is None or len(starboard_message.embeds) == 0:
            return None

        author_url = starboard_message.embeds[0].author.url

        regex_old = r"https:\/\/discordapp\.com\/channels\/\d*\/(\d*)\/(\d*)"
        regex_new = r"https:\/\/discord\.com\/channels\/\d*\/(\d*)\/(\d*)"

        match_old = re.search(regex_old, author_url)
        match_new = re.search(regex_new, author_url)

        match = match_old
        if not match_old:
            match = match_new
            if not match_new:
                return None

        channel_id = match.group(1)
        message_id = match.group(2)

        channel = starboard_message.guild.get_channel(int(channel_id))
        if channel is None:
            return None

        return await channel.fetch_message(message_id)

    async def get_starboard_message(self, original_message: discord.Message) -> discord.Message:
        """ Returns a starboard message from the original message if there is one corresponding
            Returns none otherwise
        """

        if original_message is None:
            return None

        # Looking into the history of the starboard channel and looking for an
        # embed message that has the same author url than the variable 'url'
        async for history_message in (await self.get_starboard_channel(original_message.guild)).history(limit=20):
            for embed in history_message.embeds:
                if embed.author.url == original_message.jump_url:
                    return history_message

        return None

    async def is_reaction_eligible(self, reaction) -> bool:
        """ Checks if a reaction is eligible for the starboard """

        if (self.is_control_emoji(reaction.emoji)):
            if (await self.get_starboard_channel_id(reaction.message.guild) != 0):
                return True

        return False

    async def count_stars(self, original_message : discord.Message,
                                starboard_message: discord.Message) -> int:
        """ Counts how many stars there is on the message """

        unique_users = set()

        # Counts every star on the original message
        for reaction in original_message.reactions:
            if self.is_control_emoji(reaction.emoji):
                unique_users = set(await reaction.users().flatten())
                break

        # If there is a starboard message
        if starboard_message != None:
            # adding the number of star reactions under the starboard message
            for reaction in starboard_message.reactions:
                if self.is_control_emoji(reaction.emoji):
                    unique_users |= set(await reaction.users().flatten())
                    break

        return len(unique_users)

    # Events
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):

        # No need to lock for a non starboard reaction
        if (not (await self.is_reaction_eligible(reaction))):
            return

        if (reaction.message.guild.id not in self.locks.keys()):
            self.locks[reaction.message.guild.id] = asyncio.Lock()

        async with self.locks[reaction.message.guild.id]:

            starboard_message = None
            original_message  = None

            if (await self.is_starboard_message(reaction.message)):
                starboard_message = reaction.message
                original_message  = await self.get_original_message(reaction.message)
            else:
                starboard_message = await self.get_starboard_message(reaction.message)
                original_message  = reaction.message

            stars_count = await self.count_stars(original_message, starboard_message)
            server      = self.bot.database.session.query(Server).filter(Server.discord_id == reaction.message.guild.id).first()

            if (stars_count >= server.starboard_minimum):

                content, embed = self.get_emoji_message(original_message, stars_count)

                if (starboard_message == None):
                    await (await self.get_starboard_channel(reaction.message.guild)).send(content = content, embed = embed)
                else:
                    await starboard_message.edit(content = content, embed = embed)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):

        # No need to lock for a non starboard reaction
        if (not (await self.is_reaction_eligible(reaction))):
            return

        if (reaction.message.guild.id not in self.locks.keys()):
            self.locks[reaction.message.guild.id] = asyncio.Lock()

        async with self.locks[reaction.message.guild.id]:

            starboard_message = None
            original_message  = None

            if (await self.is_starboard_message(reaction.message)):
                starboard_message = reaction.message
                original_message  = await self.get_original_message(reaction.message)
            else:
                starboard_message = await self.get_starboard_message(reaction.message)
                original_message  = reaction.message

            stars_count = await self.count_stars(original_message, starboard_message)
            server      = self.bot.database.session.query(Server).filter(Server.discord_id == reaction.message.guild.id).first()

            if (stars_count < server.starboard_minimum and starboard_message != None):
                await starboard_message.delete()

            elif (starboard_message != None):
                content, embed = self.get_emoji_message(original_message, stars_count)
                await starboard_message.edit(content = content, embed = embed)

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        
        update_starboard = False
        if (await self.get_starboard_channel_id(message.guild) != 0):
            for reaction in reactions:
                if (self.is_control_emoji(reaction.emoji)):
                    update_starboard = True
                    break

        if (not update_starboard):
            return

        if (message.guild.id not in self.locks.keys()):
            self.locks[message.guild.id] = asyncio.Lock()

        async with self.locks[message.guild.id]:
            starboard_message = None

            if (await self.is_starboard_message(message)):
                starboard_message = reaction.message

            else:
                starboard_message = await self.get_starboard_message(message)

            if (starboard_message != None):
                await starboard_message.delete()

def setup(bot):
    bot.add_cog(StarboardExt(bot))
