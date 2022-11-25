import os
import time
import discord
import asyncio
import logging
import fnmatch

from datetime                   import datetime, timezone
from typing                     import Dict, List, Optional
from discord                    import Intents
from pony.orm 	                import Database
from discord.ext                import commands
from plantbot.extension_status  import ExtensionStatus
from plantbot.database.listener import DatabaseEventListener

class PlantBot(commands.Bot):
	"""Just a plant 🌿"""

	logger	       : logging.Logger
	database       : Database       = None
	safe_mode      : bool
	debug_guild    : discord.Object = None
	extensions_root: str = "./plantbot/extensions/"

	__database_event_listeners: Dict[str, List[DatabaseEventListener]] = {}

	UNDERLINE: str = "\x1b[37;4m"
	RESET    : str = "\x1b[0m"

	def __init__(self, database: Database, *args, **kwargs) -> None:
		"""Default constructor"""

		self.database = database
		self.logger   = logging.getLogger(__name__)

		# Setting up intents
		intents = Intents.default()
		intents.emojis_and_stickers = True
		intents.message_content     = True
		intents.guilds              = True

		super().__init__(intents=intents, command_prefix='>', *args, **kwargs)

	def run(self, token: str, debug_guild: int = None, safe_mode: bool = False, *args, **kwargs) -> None:
		"""Runs the bot"""

		if debug_guild:
			self.logger.warning(f"Debug guild set to {debug_guild}, debug extensions will be loaded")
			self.debug_guild = discord.Object(id=debug_guild)

		self.safe_mode = safe_mode

		super().run(token, log_handler=None, *args, **kwargs)

	def get_extension_list(self, match: str = "*") -> List[ExtensionStatus]:
		""" Lists the extension files"""

		extensions: List[ExtensionStatus] = []

		# Walking though the full extension directory
		for root, _, files in os.walk(self.extensions_root):
			for file in files:
				if file.endswith('.py') and not file.startswith('__'):

					relative_path = os.path.join(os.path.relpath(root, self.extensions_root), file)
					relative_name = self.extension_path_to_name(relative_path)
					full_path     = os.path.join(self.extensions_root, relative_path)
					full_name     = self.extension_path_to_name(full_path)

					if fnmatch.fnmatch(full_name, match):
						extensions.append(ExtensionStatus(
							name       = relative_name,
							loaded     = full_name in self.extensions,
							identifier = full_name,
							full_path  = full_path
						))

		return extensions

	def extension_path_to_name(self, path: str) -> str:
		"""Converts a path to a name"""

		# That doesn't feel very pythonic, there must be an other way to do that
		return '.'.join(os.path.normpath(path)[:-3].split(os.path.sep))

	async def sync_tree(self) -> None:
		"""Syncs the debug guild"""

		start_time = time.time()

		if self.debug_guild:
			self.tree.copy_global_to(guild=self.debug_guild)
			await self.tree.sync(guild=self.debug_guild)
		else:
			await asyncio.gather(*[self.tree.sync(guild=guild) for guild in self.guilds], self.tree.sync())

		self.logger.info(f"Synced command tree in {round((time.time() - start_time) * 1000)}ms")

	def dispatch_db_event(self, name: str, *args, **kwargs) -> None:
		"""Dispatches a database event"""

		name = f"db_{name}"
		self.logger.debug(f"Dispatching database event {name}")
		if name in self.__database_event_listeners:
			for listener in self.__database_event_listeners[name]:
				listener.func(listener.instance, *args, **kwargs)

	def add_db_listener(self, listener: DatabaseEventListener) -> None:
		"""Adds a listener to the database"""

		if listener.name not in self.__database_event_listeners:
			self.__database_event_listeners[listener.name] = []

		self.__database_event_listeners[listener.name].append(listener)

	def remove_db_listener(self, listener: DatabaseEventListener) -> None:
		"""Removes a listener from the database"""

		if listener.name in self.__database_event_listeners:
			self.__database_event_listeners[listener.name].remove(listener)

	async def unload_extension(self, name: str, *, package: Optional[str] = None) -> bool:
		self.logger.info(f"Unloading extension {self.UNDERLINE}{name}{self.RESET}")
		try:
			await super().unload_extension(name, package=package)
		except (Exception, SyntaxError) as e:
			self.logger.exception(f"Failed to unload extension {self.UNDERLINE}{name}{self.RESET}:\n{e}")
			return False
		return True

	async def load_extension(self, name: str, *, package: Optional[str] = None) -> bool:
		self.logger.info(f"(Re)loading extension {self.UNDERLINE}{name}{self.RESET}")
		try:
			await super().load_extension(name, package=package)
		except (Exception, SyntaxError) as e:
			self.logger.exception(f"Failed to load extension {self.UNDERLINE}{name}{self.RESET}:\n{e}")
			return False
		return True

	async def reload_extension(self, name: str, *, package: Optional[str] = None) -> bool:
		try:
			await super().reload_extension(name, package=package)
		except (Exception, SyntaxError) as e:
			self.logger.exception(f"Failed to reload extension {self.UNDERLINE}{name}{self.RESET}:\n{e}")
			return False
		return True

	async def on_app_command_completion(self, interaction: discord.Interaction, _) -> None:
		"""Logs the completion of an application command"""

		elapsed = (datetime.now(timezone.utc) - interaction.created_at).total_seconds() * 1000
		self.logger.info(f"Command completed in {elapsed:,.0f} ms: {interaction.user.name}#{interaction.user.discriminator} -> /{interaction.command.qualified_name}")

	async def setup_hook(self) -> None:
		"""Setups the bot"""

		start = time.time()

		if (self.safe_mode):
			self.logger.warning("Safe mode enabled, no extensions will be loaded")
			return

		extensions  = sorted(self.get_extension_list(), key=lambda e: e.is_core, reverse=True)
		should_load = lambda e: (e.is_debug and self.debug_guild) or not e.is_debug
		await asyncio.gather(*[self.load_extension(e.identifier) for e in extensions if     e.is_core and should_load(e)])
		await asyncio.gather(*[self.load_extension(e.identifier) for e in extensions if not e.is_core and should_load(e)])

		# Syncing database and the command tree
		asyncio.create_task(self.sync_tree())

		self.logger.info(f"Setup completed in {int((time.time() - start) * 1000)} ms")
		
	async def on_ready(self) -> None:
		"""Called when the bot is ready"""

		self.logger.info(f"Logged in as {self.user.name}#{self.user.discriminator} ({self.user.id})")
		self.dispatch('database_sync')