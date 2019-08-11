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
import discord

from discord.ext import commands

from isartbot.checks.moderator          import is_moderator
from isartbot.models.server_preferences import ServerPreferences

class StarboardExt(commands.Cog):
    """ Starboard related commands and tasks """

    __slots__ = ("bot", "stars", "minimum_stars")

    def __init__(self, bot, *args, **kwargs):

        self.bot = bot

        self.minimum_stars = int(self.bot.settings.get("starboard", "minimum_stars"))

        # Sorting the stars (and conveting the keys to integers)
        self.stars = {int(k):v for k,v in self.bot.settings.items("starboard_icons")}
        self.stars = dict(sorted(self.stars.items()))

    # Commands

    @commands.group(pass_context=True)
    @commands.bot_has_permissions(send_messages=True)
    @commands.check(is_moderator)
    async def starboard(self, ctx):
        pass

    @starboard.command()
    async def set(self, ctx, channel: discord.TextChannel):
        """ Sets the current starboard channel, if none was set before, this command also enables the starboard """

        embed = discord.Embed()

        # Checking if we have enough permissions in order to operate the starboard on the designated channel
        required_perms = discord.Permissions().none()
        required_perms.update(send_messages=True, manage_messages=True, read_messages=True)

        if (not required_perms.is_subset(channel.permissions_for(ctx.guild.me))):
            embed.title       = await ctx.bot.get_translation(ctx, "failure_title")
            embed.description = f"{await ctx.bot.get_translation(ctx, 'missing_bot_perms_error')}: [send_messages, manage_messages, read_messages]"
            embed.colour      = discord.Color.red()

            await ctx.send(embed=embed)
            return
        
        self.bot.logger.info(f"Starboard set to channel {channel.id} for server named {ctx.guild.name}")

        await self.bot.database.connection.execute(
            ServerPreferences.table.update().\
                where (ServerPreferences.table.c.discord_id == ctx.guild.id).\
                values(starboard_id=channel.id)
        )

        embed.title       = await ctx.bot.get_translation(ctx, "success_title")
        embed.description = f"{await ctx.bot.get_translation(ctx, 'success_starboard_set')}: {channel.mention}"
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    @starboard.command()
    async def disable(self, ctx):
        """ Disables the starboard for the current server, use "!starboard set <channel name>" to re enable it """

        self.bot.logger.info(f"Starboard disabled for server named {ctx.guild.name}")
        
        await self.bot.database.connection.execute(
            ServerPreferences.table.update().\
                where (ServerPreferences.table.c.discord_id == ctx.guild.id).\
                values(starboard_id=0)
            )
                    
        embed = discord.Embed()
        embed.title       = await ctx.bot.get_translation(ctx, "success_title")
        embed.description = await ctx.bot.get_translation(ctx, "success_starboard_unset")
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    # Methods

    async def is_starboard_message(self, message: discord.Message) -> bool:
        """ Checks if the message is a starboard message """

        if message is None:
            return False

        # If the message is in a starboard channel
        # And if the author is the bot
        # and if the message has embeds
        if (message.author.id  == self.bot.user.id and
            message.channel.id == await self.get_server_starboard_channel_id(message.guild) and
            len(message.embeds) > 0):

            # If the author url of the first embed of the message
            # starts with 'https://discordapp.com/channels/', then it's
            # a starboard message
            return str(message.embeds[0].author.url).startswith('https://discordapp.com/channels/')

        return False

    def get_emoji_message(self, message: discord.Message, star_count : int):
        """ Returns the starboarded version of a message """

        emoji   = self.get_star_emoji(star_count)
        content = f'{emoji} **{star_count}** {message.channel.mention}'

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

        embed.timestamp = message.created_at
        embed.colour    = discord.Color.gold()
        embed.set_author(name     = message.author.display_name, 
                         url      = message.jump_url,
                         icon_url = message.author.avatar_url_as(format='png'))

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

    async def get_server_starboard_channel_id(self, server: discord.Guild) -> int:
        """ Returns the setuped starboard channel id for a given server """

        result = await self.bot.database.connection.execute(
                ServerPreferences.table.select(ServerPreferences.table.c.discord_id == server.id)
            )
        servers = await result.fetchall()

        # Something is wrong, either the server is not registered in the database, 
        # either there is more than one server with this id, which shouldn't be possible
        if (len(servers) != 1):
            self.bot.logger.warning("Starboard configuration ambiguity ! Please check the database integrity.")
            return 0

        server = servers[0]

        return server[ServerPreferences.table.c.starboard_id]

    async def get_server_starboard_channel(self, server: discord.Guild) -> discord.TextChannel:

        channel_id = await self.get_server_starboard_channel_id(server)

        if (channel_id != 0):
            return server.get_channel(channel_id)

        return None

    async def is_reaction_eligible(self, reaction) -> bool:
        """ Checks if a reaction is eligible for the starboard """

        # Retreiving the emoji code ex.: ":star:"
        reaction_emoji = reaction.emoji
        if isinstance(reaction_emoji, str):
            reaction_emoji = emoji.demojize(reaction_emoji)
        else:
            reaction_emoji = reaction_emoji.name

        if (reaction_emoji == self.bot.settings.get('starboard', 'control_emoji')):
            if (await self.get_server_starboard_channel_id(reaction.message.guild) != 0):
                return True
        
        return False

    # Events

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        self.bot.logger.info(f"Added reaction: {reaction.emoji}, {user.name}, {await self.is_reaction_eligible(reaction)}")

        if (await self.is_reaction_eligible(reaction)):
            content, embed = self.get_emoji_message(reaction.message, 1)
            channel = await self.get_server_starboard_channel(reaction.message.guild)

            await channel.send(content = content, embed = embed)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        self.bot.logger.info(f"Removed reaction: {reaction.emoji}, {user.name} {await self.is_reaction_eligible(reaction)}")

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        self.bot.logger.info(f"Cleared reactions: {reactions}")

def setup(bot):
    bot.add_cog(StarboardExt(bot))
