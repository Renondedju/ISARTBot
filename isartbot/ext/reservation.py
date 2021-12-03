# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018 - 2021 Renondedju

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
import os
import json
import discord

from datetime                       import datetime, timedelta
from dataclasses                    import dataclass
from discord.ext                    import tasks, commands
from sqlalchemy.sql.expression import true
from isartbot.helper                import Helper
from googleapiclient.discovery      import build
from google.oauth2.credentials      import Credentials
from google_auth_oauthlib.flow      import InstalledAppFlow
from google.auth.transport.requests import Request

class ReservationExt(commands.Cog):
    """ Helps to create and check room reservation """

    @dataclass
    class Reservation:
        date: datetime
        name: str
        status: str
        location: str

        def __str__(self) -> str:
            date = self.date.strftime("%d/%m %H:%M")
            
            return f"{date} - {self.name} ({self.location}) - {self.status}"


    def __init__(self, bot):
        self.bot = bot
        
        self.creds = self.load_credentials()

        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)

        self.event_statuses = self.build_event_statuses()

        self.reservation_scan.start()

    def cog_unload(self):
        self.reservation_scan.cancel()

    def load_credentials(self):
        creds = None
        google_token_file_name = self.bot.settings.get('reservation', 'google_token')

        if os.path.exists(google_token_file_name):
            creds = Credentials.from_authorized_user_file(google_token_file_name)
        
        if (not creds or not creds.valid):
            if (creds and creds.expired and creds.refresh_token):
                creds.refresh(Request())
            else:
                scopes = json.loads(self.bot.settings.get('reservation', 'google_api_scopes'))
                google_credentials_file_name = self.bot.settings.get('reservation', 'google_credentials')

                flow = InstalledAppFlow.from_client_secrets_file(google_credentials_file_name, scopes)

                creds = flow.run_local_server(port=0)
            with open(google_token_file_name, 'w') as token:
                token.write(creds.to_json())
                
        return creds

    def build_event_statuses(self):
        event_statuses = {}
        
        for (key, icon) in self.bot.settings.items('reservation_icons'):
            event_statuses['(' + self.bot.settings.get('reservation', key) + ')'] = icon

        return event_statuses

    @tasks.loop(hours=4 * 24.0)
    async def reservation_scan(self):
        return

    @reservation_scan.before_loop
    async def pre_reservation_scan(self):
        await self.bot.wait_until_ready()

    @commands.group(invoke_without_command=True, pass_context=True,
        help="reservation_help", description="reservation_description")
    async def reservation(self, ctx):
        await ctx.send_help(ctx.command)

    @reservation.command(help="reservation_list_help", description="reservation_list_description")
    async def list(self, ctx, page=1):
        """" Lists all current reservations on the Google Calendar with their status """

        if (self.calendar_service == None):
            await Helper.send_error(ctx, ctx.channel, 'reservation_list_error')

        now = datetime.utcnow()

        events = self.calendar_service.events().list(calendarId=self.bot.settings.get('reservation', 'calendar_id'), 
            timeMin=now.isoformat() + 'Z', singleEvents=True, orderBy='startTime').execute()

        event_list = []

        regex = "([(].*[)]|\b" + self.bot.settings.get('reservation', 'unavailable') + "\b)"

        for event in events['items']:
            splitted_summary = re.split(regex, event['summary'])

            name = splitted_summary[0]
            date = datetime.strptime(event['start']['dateTime'], '%Y-%m-%dT%H:%M:%S+01:00')
            status = splitted_summary[1] if len(splitted_summary) > 1 else "?"
            location = event['location'] if 'location' in event else "?"

            event_list.append(self.Reservation(
                name = name,
                date = date,
                status = self.event_statuses[status] if status in self.event_statuses else "?",
                location = location
            ))

        await ctx.send(embed=discord.Embed(
            description = '\n'.join([str(event) for event in event_list]),
            title = await ctx.bot.get_translation(ctx, 'reservation_list_title'),
            color = discord.Color.green()
        ))

    @reservation.command(help="reservation_notify_help", description="reservation_notify_description")
    async def notify(self, ctx):
        """" Sends a mail for validation if the last one is old enough. Remember that a mail is already sent regularly. """
        
        await Helper.send_success(ctx, ctx.channel, 'reservation_notify_success')

def setup(bot):
    bot.add_cog(ReservationExt(bot))
    