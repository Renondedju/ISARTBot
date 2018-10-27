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

import discord
import asyncio
import twitch

from isartbot.exceptions import CogLoadingFailed

class TwitchAlerts():
    """ Twitch alerts class, mainly used for E-SART Dragons 
    
        https://www.twitch.tv/esartdragons
    """

    def __init__(self, bot):

        #Private
        self.bot = bot

        #Fetching parameters
        self.notification_message = self.bot.settings.get('notification_message', command = 'twitch_alerts')
        self.announce_channel_id  = self.bot.settings.get('announce_channel_id' , command = 'twitch_alerts')
        self.refresh_delay        = self.bot.settings.get('refresh_delay'       , command = 'twitch_alerts')
        self.channel_name         = self.bot.settings.get('channel_name'        , command = 'twitch_alerts')
        self.twitch_token         = self.bot.settings.get('twitch_token'        , command = 'twitch_alerts')
        self.enabled              = self.bot.settings.get('enabled'             , command = 'twitch_alerts')
        
        self.message = None
        self.announce_channel = self.bot.get_channel(self.announce_channel_id)

        # If something failed
        if self.bot.guild.id is None or self.announce_channel is None:
            raise CogLoadingFailed('Failed to load one or more settings')

        self.task = self.bot.loop.create_task(self.notification_task())

    def __unload(self):
        self.task.cancel()

    async def notification_task(self):

        prev_stream_state = []
        helix             = twitch.helix.api.TwitchHelix(client_id=self.twitch_token)

        while(self.refresh_delay != 1):
            await asyncio.sleep(self.refresh_delay)

            current_stream_state = helix.get_streams(user_logins=[self.channel_name])

            # checking if the stream started (raising edge)
            if len(prev_stream_state) == 0 and len(current_stream_state) != 0:
                await self.on_stream_start(current_stream_state[0], 
                    helix.get_games(game_ids=current_stream_state[0]['game_id']))

            # checking if the stream stopped (falling edge)
            elif len(prev_stream_state) != 0 and len(current_stream_state) == 0:
                await self.on_stream_stop(prev_stream_state[0])
            
            prev_stream_state = current_stream_state

        self.bot.logs.print('Twitch notification loop exited !')

    async def on_stream_start(self, stream, game):
        """ Event triggered when a stream starts """

        await self.send_notification(stream, game)
        self.bot.logs.print('Twitch stream started !')

    async def on_stream_stop(self, stream):
        """ Event trigerred when a stream stops """

        self.bot.logs.print('Twitch stream stopped !')

    async def send_notification(self, stream, game):
        """ Sends a notification message """

        embed = discord.Embed()
        embed.set_author(
            name="E-SART Dragons",
            icon_url="https://static-cdn.jtvnw.net/jtv_user_pictures/twitch-profile_image-8a8c5be2e3b64a9a-70x70.png")
        embed.url   = "https://www.twitch.tv/esartdragons"
        embed.title = stream['title']
        embed.set_thumbnail(url="https://pbs.twimg.com/profile_images/1016327266240991233/9qz6aCD9_400x400.jpg")
        embed.set_footer(text="Type \"!iam stream\" to get notified next time !")

        if (len(game) != 0):
            embed.add_field(name='Game', value=game[0]['name'])

        self.message = await self.announce_channel.send(self.notification_message, embed=embed)

def setup(bot):
    bot.add_cog(TwitchAlerts(bot))