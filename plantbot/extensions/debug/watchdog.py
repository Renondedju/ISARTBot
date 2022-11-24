import asyncio

from typing       import List
from logging 	  import Logger, getLogger
from plantbot.bot import PlantBot, ExtensionStatus
from watchfiles   import awatch, DefaultFilter, Change
from discord.ext  import commands

class Watchdog(commands.Cog):
	"""Reloads loaded extensions when they are saved to disk"""

	bot   : PlantBot
	logger: Logger
	filter: DefaultFilter

	def __init__(self, bot: PlantBot):
		self.bot 		   = bot
		self.logger 	   = getLogger(__name__)

		# Silencing the watchfiles logger
		getLogger('watchfiles').setLevel(100)

	async def watch(self) -> None:
		"""Runs the watchdog"""

		extensions: List[ExtensionStatus] = self.bot.get_extension_list()

		async for changes in awatch(self.bot.extensions_root, poll_delay_ms=1000):

			# Iterating over the changes from oldest to newest
			for change in sorted(changes, reverse=True):
				change_type: Change          = change[0]
				change_path: str             = change[1]
				extension  : ExtensionStatus = next((extension for extension in extensions if extension.full_path in change_path), None)

				# Ignore changes to files that aren't extensions
				if extension is None:
					continue

				try:
					if change_type == Change.deleted and extension.loaded:
						await self.bot.unload_extension(extension.identifier)
						await self.bot.sync_tree()
					elif change_type == Change.added and not extension.loaded:
						await self.bot.load_extension(extension.identifier)
						await self.bot.sync_tree()
					elif change_type == Change.modified and change_type != (Change.added or Change.deleted):
						if extension.loaded:
							await self.bot.reload_extension(extension.identifier)
						else:
							await self.bot.load_extension(extension.identifier)

				except Exception as e:
					self.logger.exception(e)

				finally:
					extensions = self.bot.get_extension_list()

async def setup(bot: PlantBot):
	watchdog = Watchdog(bot)
	await bot.add_cog(watchdog)
	asyncio.create_task(watchdog.watch())