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
import asyncio
import discord
import feedparser

from bs4                     import BeautifulSoup
from discord.ext             import commands
from isartbot.exceptions     import EmptyRssFeed, AlreadyExistingFeed, CogLoadingFailed
from isartbot.bot_decorators import is_admin

class Rss():
    """ Rss task and commands class """

    def __init__(self, bot):

        self.bot          = bot
        self.feeds        = bot.settings.get('feeds',        command = 'rss')
        self.channel_id   = bot.settings.get('channel_id'  , command = 'rss')
        self.refresh_rate = bot.settings.get('refresh_rate', command = 'rss')
        self.rss_channel  = bot.get_channel(self.channel_id)

        if self.rss_channel is None:
            raise CogLoadingFailed('Rss channel is None !')

        self.task = self.bot.loop.create_task(self.rss_task())

    def __unload(self):
        self.task.cancel()

    @commands.group(pass_context=True, invoke_without_command=True, hidden=True)
    @commands.check(is_admin)
    async def rss(self, ctx):
        """ simple rss command group """
        pass

    def remove_feed(self, feed_url : str):
        """ Removes a rss feed to the list of listened feeds
        
            returns True if the feed has successfully been removed,
            False otherwise
        """

        self.feeds = self.bot.settings.get('feeds', command = 'rss')

        feed_removed = False

        for feed in self.feeds:
            if feed['url'] == feed_url:
                self.feeds.remove(feed)
                feed_removed = True
                break

        self.bot.settings.write(self.feeds, 'feeds', command = 'rss')

        return feed_removed

    def add_feed(self, feed_url : str, logo : str):
        """ Adds a rss feed to the list of listened feeds
        
            Raises:
                EmptyRssFeed        - Feed is empty
                AlreadyExistingFeed - Feed already exists in the list
        """

        self.feeds = self.bot.settings.get('feeds', command = 'rss')
        urls = [feed['url'] for feed in self.feeds]

        if feed_url in urls:
            raise AlreadyExistingFeed

        if len(feedparser.parse(feed_url).entries) == 0:
            raise EmptyRssFeed

        self.feeds.append({'url' : feed_url, 'logo' : logo})
        self.bot.settings.write(self.feeds, 'feeds', command = 'rss')

        return

    def clean_html(self, raw_text : str) -> str:
        """ Cleans the html content from the input """

        soup = BeautifulSoup(raw_text,  'lxml')
        soup = BeautifulSoup(soup.text, 'lxml')
        
        #We are doing the parsing 2 times since some feeds sends chars like '&lt;'
        # wish gets converted to '<' or others special html chars.

        return soup.text.replace('\n', ' ')

    def get_entry_embed(self, feed, entry, logo) -> discord.Embed:
        """ Returns the discord embed for an rss entry """

        feed_url = feed.feed.get('link', '')
        if not feed_url.startswith('http'):
            feed_url = ''

        embed = discord.Embed()
        embed.set_author(
            name=feed.feed.get('title', 'Unknown'), 
            icon_url=logo,
            url=feed_url)
        embed.set_footer(text=entry.get('published', '')[:25])

        embed.title       = self.clean_html(entry.get('title'  , discord.Embed.Empty))[:255]
        embed.description = self.clean_html(entry.get('summary', discord.Embed.Empty))[:800]

        embed.color = discord.Color.blue()

        if len(embed.description) > 1000:
            embed.description += '...'

        embed.description += ' [Lire la suite]({})'.format(
            entry.get('link',
            feed.feed.get('link', 'https://www.google.com/')))

        images = entry.get('media_thumbnail', [])
        if len(images) > 0:
            embed.set_image(url=images[0].get('url', ''))
        else:
            links = entry.get('links', [])

            for link in links:
                if link.get('type', '').startswith('image/'):
                    embed.set_image(url=link.get('href', ''))
                    break
                    
        return embed

    async def has_been_posted(self, entry) -> bool:
        """ Checks if an entry has already been posted or not """

        # The plus 5 is just to make sure 
        count = len(self.feeds) * self.max_entries_count + 5

        async for message in self.rss_channel.history(limit = count):
            for embed in message.embeds:
                if embed.title == self.clean_html(entry.get('title', ''))[:255]:
                    return True

        return False

    async def update_feeds(self):
        """ Updates all the feeds and posts them if needed """

        #Showing activity 
        async with self.rss_channel.typing():
            
            #Updating rss feeds
            for feed in self.feeds:
                parsed_feed = feedparser.parse(feed['url'])
                for entry in parsed_feed.entries:
                    #For each entry not posted : post it !
                    if (not await self.has_been_posted(entry)):

                        embed = self.get_entry_embed(parsed_feed, entry, feed['logo'])
                        await self.rss_channel.send(embed = embed)

                        self.bot.logs.print('Sent a new rss entry : '
                            + entry.get('title', 'unknown'))

    #Commands
    @rss.command()
    async def add(self, ctx, feed_url, logo = ""):
        """ Adds a rss feed to the list of listened feeds """

        self.add_feed(feed_url, logo)

        await self.bot.send_success(ctx,
            "Successfully added the feed to the followed list",
            "Rss feed")

    @rss.command()
    async def test(self, ctx):
        """ Test the rss embed """

        feed = feedparser.parse(self.feeds[2]['url'])

        for i in range(3):
            embed = self.get_entry_embed(feed, feed.entries[i],
                self.feeds[2]['logo'])

            await ctx.send(embed = embed)

    @rss.command()
    async def update(self, ctx):
        
        async with ctx.message.channel.typing():
            await self.update_feeds()

        await self.bot.send_success(ctx,
            'Feeds has successfully been updated',
            'Rss feeds')

    @rss.command()
    async def remove(self, ctx, *, feed_url):
        """ Adds a rss feed to the list of listened feeds """

        result = self.remove_feed(feed_url)

        if not result:
            await self.bot.send_fail(ctx,
                "This feed does not exists, use ``{}rss list`` to get a  list "
                "of all the feeds followed.".format(self.bot.command_prefix),
                "Rss feed")
            return

        await self.bot.send_success(ctx,
            "Successfully removed the feed of the followed list",
            "Rss feed")

    @add.error
    async def add_error(self, ctx, error):

        error = getattr(error, 'original', error)

        if isinstance(error, EmptyRssFeed):
            await self.bot.send_fail(ctx,
                "The rss feed you tried to add seems to be empty",
                "Rss feed")
            return
        
        if isinstance(error, AlreadyExistingFeed):
            await self.bot.send_fail(ctx,
                "The rss feed you tried to add is already in the followed ones",
                "Rss feed")
            return

        await self.bot.on_error(ctx, error)

    async def rss_task(self):
        """ main rss task. """

        while (True):

            #wait for a fixed amount of sec before doing a refresh
            await self.update_feeds()
            await asyncio.sleep(self.refresh_rate)

def setup(bot):
    bot.add_cog(Rss(bot))