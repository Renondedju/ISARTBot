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
import base64
import discord

from datetime                       import datetime, timedelta
from dataclasses                    import dataclass
from discord.ext                    import tasks, commands
from email.mime.text                import MIMEText
from isartbot.checks                import is_club_manager
from isartbot.helper                import Helper
from email.mime.multipart           import MIMEMultipart
from googleapiclient.discovery      import build
from google.oauth2.credentials      import Credentials
from google_auth_oauthlib.flow      import InstalledAppFlow
from google.auth.transport.requests import Request

class ReservationExt(commands.Cog):
    """ Assists club managers for room reservation """

    __slots__ = ("bot", "creds", "calendar_service", "gmail_service", "event_statuses")

    @dataclass
    class Reservation:
        date: datetime
        name: str
        status: str
        location: str

        def __str__(self) -> str:
            date = self.date.strftime("%d/%m %H:%M")
            
            return f"{date} - {self.name} ({self.location}) - {self.status}"

        def get_mail_format(self):
            date = self.date.strftime("le %d/%m à %Hh%M")

            return f"- {self.name}{date} ({self.location})"

    def __init__(self, bot):
        self.bot = bot
        
        self.creds = self.load_credentials()

        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)

        self.event_statuses = self.build_event_statuses()

        self.reservation_scan.change_interval(hours=self.bot.settings.getint('reservation', 'mailing_delay') * 24 )
        self.reservation_scan.start()

    def cog_unload(self):
        self.reservation_scan.cancel()

    def load_credentials(self):
        """" Loads Google credentials and writes them in a file for future loadings """

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
        """" Associates a reservation status with an icon """

        event_statuses = {}
        
        for (key, icon) in self.bot.settings.items('reservation_icons'):
            event_statuses[self.bot.settings.get('reservation', key)] = icon

        return event_statuses

    @tasks.loop(hours=4 * 24.0)
    async def reservation_scan(self):
        """ Sends a mail containing all pending reservations """

        if self.gmail_service == None:
            return

        event_list = await self.get_events_from_calendar()
        pending_status = self.bot.settings.get('reservation_icons', 'pending')
        reservation_lines = '\n'.join([event.get_mail_format() for event in event_list if event.status == pending_status])

        mail_template_path = self.bot.settings.get('reservation', 'mail_template')

        if os.path.exists(mail_template_path):
            with open(mail_template_path, encoding='utf-8') as mail_template_file:
                mail_content = mail_template_file.read().format(reservation_lines)

                mime_message = MIMEMultipart()
                mime_message['subject'] = self.bot.settings.get('reservation', 'mail_title')
                mime_message['to'] = self.bot.settings.get('reservation', 'destination_mail')
                mime_message.attach(MIMEText(mail_content, 'plain'))

                message = {'raw': base64.urlsafe_b64encode(mime_message.as_bytes()).decode(encoding='utf-8')}

                try:
                    self.gmail_service.users().messages().send(userId=self.bot.settings.get('reservation', 'sender_mail'), 
                        body=message).execute()
                except:
                    self.bot.logger.info("Failed to send the mail for validation")

    @reservation_scan.before_loop
    async def pre_reservation_scan(self):
        await self.bot.wait_until_ready()

    @commands.group(invoke_without_command=True, pass_context=True,
        help="reservation_help", description="reservation_description")
    @commands.check(is_club_manager)
    async def reservation(self, ctx):
        await ctx.send_help(ctx.command)

    @reservation.command(help="reservation_list_help", description="reservation_list_description")
    @commands.check(is_club_manager)
    async def list(self, ctx):
        """" Lists all current reservations on the Google Calendar with their status """

        if (self.calendar_service == None):
            await Helper.send_error(ctx, ctx.channel, 'reservation_list_error')

        event_list = await self.get_events_from_calendar()

        await ctx.send(embed=discord.Embed(
            description = '\n'.join([str(event) for event in event_list]),
            title = await ctx.bot.get_translation(ctx, 'reservation_list_title'),
            color = discord.Color.green()
        ))

    @reservation.command(help="reservation_notify_help", description="reservation_notify_description")
    @commands.check(is_club_manager)
    async def notify(self, ctx):
        """" Sends a mail containing all pending reservations. Remember that a mail is already sent regularly. """
        
        if self.gmail_service == None:
            await Helper.send_error(ctx, ctx.channel, 'reservation_notify_error')

        await Helper.ask_confirmation(ctx, ctx.channel, 'reservation_notify_confirmation_title',
            initial_content='reservation_notify_confirmation_description', success_content='reservation_notify_success',
            failure_content='reservation_notify_aborted')

        event_list = await self.get_events_from_calendar()
        pending_status = self.bot.settings.get('reservation_icons', 'pending')
        reservation_lines = '\n'.join([event.get_mail_format() for event in event_list if event.status == pending_status])

        mail_template_path = self.bot.settings.get('reservation', 'mail_template')

        if os.path.exists(mail_template_path):
            with open(mail_template_path, encoding='utf-8') as mail_template_file:
                mail_content = mail_template_file.read().format(reservation_lines)

                mime_message = MIMEMultipart()
                mime_message['subject'] = self.bot.settings.get('reservation', 'mail_title')
                mime_message['to'] = self.bot.settings.get('reservation', 'destination_mail')
                mime_message.attach(MIMEText(mail_content, 'plain'))

                message = {'raw': base64.urlsafe_b64encode(mime_message.as_bytes()).decode(encoding='utf-8')}

                try:
                    self.gmail_service.users().messages().send(userId=self.bot.settings.get('reservation', 'sender_mail'), 
                        body=message).execute()
                except:
                    await Helper.send_error(ctx, ctx.channel, 'reservation_notify_send_error')
        else:
            await Helper.send_error(ctx, ctx.channel, 'reservation_notify_template_error')

    async def get_events_from_calendar(self):
        """ Returns all current reservations """

        now = datetime.utcnow()

        events = self.calendar_service.events().list(calendarId=self.bot.settings.get('reservation', 'calendar_id'), 
            timeMin=now.isoformat() + 'Z', singleEvents=True, orderBy='startTime').execute()

        event_list = []

        for event in events['items']:
            splitted_summary = re.split("([(].*[)])", event['summary'])

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

        return event_list

def setup(bot):
    bot.add_cog(ReservationExt(bot))
    