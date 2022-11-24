import json
import random
import discord
import logging

from typing 		import List
from discord 	    import app_commands
from discord.ext    import commands
from datetime       import datetime, timedelta
from dataclasses    import dataclass
from plantbot.bot   import PlantBot
from urllib.parse   import quote
from urllib.request import urlopen

@dataclass
class FoodtruckEntry:
	name: str
	link: str
	date: datetime
	description: str

	def __str__(self) -> str:
		link = self.link or f"https://www.google.com/search?q={quote(self.name, safe='')}"

		return f"[{self.name} ({self.description})]({link})"

	def __repr__(self) -> str:
		return f"FoodtruckEntry({self.name}, {self.link}, {self.date}, {self.description})"

class Foodtruck(commands.Cog):

	bot        : PlantBot
	logger     : logging.Logger
	cache      : List[FoodtruckEntry] = None
	last_update: datetime             = datetime.now()

	empty_strings: List[str] = [
		"Our foodtruck is in another castle...",
		"Foodtrucks are for the weak",
		"Triangle sandwiches are nice too",
		"Pastabox à l'ancienne",
		"Rien, mange ta main"
	]

	def __init__(self, bot: PlantBot):
		self.bot    = bot
		self.logger = logging.getLogger(__name__)
		self.cache  = self.get_foodtrucks()

	def get_foodtrucks_from_servers(self) -> List[FoodtruckEntry]:
		"""Returns the foodtrucks from the isart servers"""

		foodtrucks: List[FoodtruckEntry] = None

		# Retry 3 times if the request fails
		for i in range(3):
			try:
				with urlopen("https://my.isartdigital.com/api/foodtruck") as response:
			
					# Parsing json into a list of Foodtruck objects and sorting them by date
					data       = json.loads(response.read().decode('utf-8'))
					foodtrucks = sorted([FoodtruckEntry(
						date        = datetime.strptime(foodtruck['jour'], "%Y-%m-%d").date(),
						name        = foodtruck['nom'].capitalize(),
						description = foodtruck['description'],
						link        = foodtruck['lien']) 
						
						for foodtruck in data
					], key=lambda foodtruck: foodtruck.date)

				break
			except Exception as e:
				self.logger.exception(e)

			self.logger.debug(f"Failed to fetch foodtrucks from servers ({i}/3)")
		
		return foodtrucks

	def get_foodtrucks(self) -> List[FoodtruckEntry]:
		"""Queries the https://my.isartdigital.com/api/foodtruck endpoint and returns it's parsed json data"""

		# If the cache is not empty and the last update was less than 5 minutes ago, return the cache
		if self.cache and (datetime.now() - self.last_update) < timedelta(minutes=5):
			return self.cache

		# Otherwise, fetch from the servers
		foodtrucks = self.get_foodtrucks_from_servers()

		# Checking if the cache contains the same entries as the new data
		if self.cache != foodtrucks:
			self.logger.debug(f"Foodtrucks cache updated {foodtrucks}")
			self.last_update = datetime.now()
			self.cache = foodtrucks
			
		return foodtrucks

	def prettify_time(self, seconds: float) -> str:
		"""Returns a string representing the time in a human readable format"""

		return (
			f"{int(seconds)} seconds" if seconds < 60 else
			f"{int(seconds/60)} minutes" if seconds < 3600 else
			f"{int(seconds/3600)} hours" if seconds < 86400 else
			f"{int(seconds/86400)} days"
		)

	@app_commands.command()
	async def foodtruck(self, interaction: discord.Interaction) -> None:
		"""Gets the current food truck schedule"""

		# Fetch the current data
		today      = datetime.now().date()
		foodtrucks = self.get_foodtrucks()

		# Getting the first foodtruck of the day
		todays_foodtruck    = next((foodtruck for foodtruck in foodtrucks if foodtruck.date == today), None)
		upcoming_foodtrucks = [foodtruck for foodtruck in foodtrucks if foodtruck.date > today]
		
		today_str    = f"**{todays_foodtruck}**" if todays_foodtruck else f"Nothing - *{random.choice(self.empty_strings)}*"
		upcoming_str = "*Nothing planned yet* ¯\_(ツ)_/¯"
		if len(upcoming_foodtrucks) > 0:
			upcoming_str = "\n".join([f"`{foodtruck.date.strftime('%a %d %b')}` | {foodtruck}" for foodtruck in upcoming_foodtrucks])

		embed = discord.Embed(
			description = f"\U0001f355 **Today's Truck**\n{today_str}\n\n**\u23F3 Upcoming**\n{upcoming_str}",
			color       = discord.Color.brand_green(),
		)

		# Get relative time since last update
		embed.set_footer(text=f"Last update {self.prettify_time((datetime.now() - self.last_update).total_seconds())} ago")

		await interaction.response.send_message(embed=embed)

async def setup(bot: PlantBot) -> None:
	await bot.add_cog(Foodtruck(bot))