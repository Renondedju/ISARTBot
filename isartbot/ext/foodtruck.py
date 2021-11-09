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

import json
import discord

from datetime       import datetime
from discord.ext    import commands
from urllib.request import urlopen
from dataclasses    import dataclass

class FoodtruckExt(commands.Cog):

	@dataclass()
	class Foodtruck:
		name: str
		link: str
		date: datetime
		description: str

		def __str__(self) -> str:
			delimiters = "**" if self.date == datetime.today().date() else ""

			return f"{delimiters}{self.date.strftime('%d/%m')} - [{self.name}]({self.link}) ({self.description}) {delimiters}"

	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True, help="foodtruck_help", description="foodtruck_description")
	async def foodtruck(self, ctx):
		
		# Getting the foodtrucks
		lines = [str(foodtruck) for foodtruck in self.get_foodtrucks()] or [await ctx.bot.get_translation(ctx, 'foodtruck_list_empty')]

		# Sending the embed
		await ctx.send(embed= discord.Embed(
			description = "\n".join(lines),
			title       = await ctx.bot.get_translation(ctx, 'foodtruck_list_title'),
			color       = discord.Color.green()
		))

	def get_foodtrucks_link(self, name: str) -> str:
		"""Returns the link to the foodtruck's socials """
		
		# Dictionary of foodtruck's names and their links
		return {
			"ida's truck"       : "https://www.facebook.com/IdasFoodtruck",
			"kay fritay"        : "https://www.facebook.com/kayfritay",
			"la cocotte mobile" : "https://www.facebook.com/La-cocotte-mobile-247388968767076/",
			"tuK tuk food truck": "https://www.facebook.com/tuktukfoodtruckthai/",
			"pizza tony"        : "https://www.facebook.com/lescamionspizzatony/",
			"le Trotter"        : "https://www.facebook.com/letrotter.fr/",
			"la mobylette verte": "https://www.facebook.com/mobyletteverte/"
		}.get(name.lower(), "")

	def get_foodtrucks(self):
		"""Queries the https://my.isartdigital.com/api/foodtruck endpoint and returns it's parsed json data"""
	
		with urlopen("https://my.isartdigital.com/api/foodtruck") as response:
			# Parsing json into a list of Foodtruck objects
			foodtrucks = [self.Foodtruck(
				date        = datetime.strptime(foodtruck['jour'], "%Y-%m-%d").date(),
				name        = foodtruck['nom'].capitalize(),
				description = foodtruck['description'],
				link        = self.get_foodtrucks_link(foodtruck['nom'])) for foodtruck in json.loads(response.read().decode('utf-8'))]

		# Ordering the foodtrucks by date
		return sorted(foodtrucks, key=lambda foodtruck: foodtruck.date)

def setup(bot):
	bot.add_cog(FoodtruckExt(bot))