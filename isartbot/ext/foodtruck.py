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

import os
import csv
import discord
import asyncio

from datetime        import datetime
from discord.ext     import commands
from isartbot.checks import is_super_admin
from isartbot.helper import Helper

class FoodtruckExt(commands.Cog):

    def __init__(self, bot):
        self.bot     = bot
        self.db_path = self.bot.settings.get("foodtruck", "database") 

    @commands.group(pass_context=True, invoke_without_command=True,
        help="foodtruck_help", description="foodtruck_description")
    async def foodtruck(self, ctx):
        
        # if a subcommand is passed
        if not ctx.invoked_subcommand is None:
            return

        today      = datetime.today().date()
        fmt        = await ctx.bot.get_translation(ctx, 'foodtruck_list_format')
        foodtrucks = self.get_foodtrucks(today)

        # Filling the embed content
        lines = list()
        for truck in foodtrucks:
            delimiters = "**" if self.parse_truck_date(truck) == today else ""
            truck['date'] = truck['date'][:5]
            lines.append(fmt.format(delimiters=delimiters, **truck))

        if (len(foodtrucks) == 0):
            lines.append(await ctx.bot.get_translation(ctx, 'foodtruck_list_empty'))

        embed = discord.Embed()
        embed.description = '\n'.join(lines)
        embed.title       = await ctx.bot.get_translation(ctx, 'foodtruck_list_title')
        embed.color       = discord.Color.green()

        await ctx.send(embed=embed)
        
    @foodtruck.command(help="foodtruck_upload_help", description="foodtruck_upload_description")
    @commands.check(is_super_admin)
    async def upload(self, ctx):
        """ Uploads a new database to the bot """

        if (len(ctx.message.attachments) != 1):
            await Helper.send_error(ctx, ctx.channel, "foodtruck_upload_attachment_error")
            return

        try:
            if (not os.path.exists(os.path.dirname(self.db_path))):
                os.makedirs(os.path.dirname(self.db_path))

            # Saving the attachment
            await ctx.message.attachments[0].save(self.db_path)
            await Helper.send_success(ctx, ctx.channel, "foodtruck_upload_succeeded")
        except:
            await Helper.send_error(ctx, ctx.channel, "foodtruck_upload_failed")

    # Methods
    def get_foodtrucks(self, target_date):

        foodtrucks = list()
        with open(self.db_path, newline='', encoding="utf-8") as csv_file:
            for truck in csv.DictReader(csv_file):
                delta = (self.parse_truck_date(truck) - target_date).days
                
                if (delta >= 0 and delta <= 7):
                    foodtrucks.append(truck)
        
        return foodtrucks

    def parse_truck_date(self, truck):
        return datetime.strptime(truck['date'], "%d/%m/%Y").date()

def setup(bot):
    bot.add_cog(FoodtruckExt(bot))