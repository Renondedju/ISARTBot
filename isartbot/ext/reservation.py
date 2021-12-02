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

import discord

from datetime       import datetime
from dataclasses    import dataclass
from discord.ext    import tasks, commands

class ReservationExt(commands.Cog):

    @dataclass
    class Reservation:
        date: datetime
        location: str

    """ Helps to create and check room reservation """
    def __init__(self, bot):
        self.bot = bot
        self.reservation_scan.start()

    def cog_unload(self):
        self.reservation_scan.cancel()

    @tasks.loop(minutes=10.0)
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
        await ctx.send(embed=discord.Embed(
            description = "ToDo",
            title = await ctx.bot.get_translation(ctx, 'reservation_list_title'),
            color = discord.Color.green()
        ))

def setup(bot):
    bot.add_cog(ReservationExt(bot))
    