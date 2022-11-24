import logging
from typing 					import ClassVar, Dict
from discord.ext 			    import commands
from plantbot.database.listener import DatabaseEventListener
from plantbot.bot 			    import PlantBot

class MetaExtension(commands.CogMeta):
	"""Meta class for extensions"""
	
	logger: logging.Logger
	__plantbot_db_listeners__: Dict[str, DatabaseEventListener]

	def __new__(cls, *args, **kwargs):

		name, bases, attrs = args
		new_cls = super().__new__(cls, name, bases, attrs, **kwargs)

		listeners = {}

		# Collecting database event listeners
		for base in reversed(new_cls.__mro__):
			for elem, value in base.__dict__.items():
				# Check if the element is a DatabaseEventListener
				if isinstance(value, DatabaseEventListener):
					listeners[value.name] = value

		new_cls.__plantbot_db_listeners__ = listeners
		new_cls.logger = logging.getLogger(f"{new_cls.__module__}")

		return new_cls

class Extension(commands.Cog, metaclass=MetaExtension):
	"""A plantbot extension, see discord.ext.commands.Cog"""

	bot   : PlantBot
	logger: logging.Logger

	__plantbot_db_listeners__: Dict[str, DatabaseEventListener]

	def __init__(self, bot: PlantBot) -> None:
		self.bot = bot

		for listener in self.__plantbot_db_listeners__.values():
			listener.instance = self

	def cog_load(self) -> None:
		"""Called when the extension is loaded"""

		for listener in self.__plantbot_db_listeners__.values():
			self.bot.add_db_listener(listener)
		
	def cog_unload(self) -> None:
		"""Called when the extension is unloaded"""

		for listener in self.__plantbot_db_listeners__.values():
			self.bot.remove_db_listener(listener)

	@classmethod
	def db_listener(cls, event: str = None):
		"""Transforms the function into a database event listener"""

		def decorator(func):
			return DatabaseEventListener(name=event or func.__name__, func=func)

		return decorator

class GroupExtension(Extension, metaclass=MetaExtension):
	"""A plantbot group extension, see discord.ext.commands.GroupCog"""

	__cog_is_app_commands_group__: ClassVar[bool] = True