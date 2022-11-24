import discord

from pony.orm     				import Optional, Set, Required, PrimaryKey
from plantbot.database.instance import database
from plantbot.instance			import plantbot

class Guild(database.Entity):
	""" Discord guild settings """

	def __init__(self, guild: discord.Guild, **kwargs) -> None:
		super().__init__(discord_id = guild.id, **kwargs)

	# Discord guild ID
	discord_id = PrimaryKey(int, auto=False, size=64)

	# Auto maintenance entities
	text_channels = Set('TextChannel', reverse='guild', cascade_delete=True)
	roles         = Set('Role'       , reverse='guild', cascade_delete=True)
	
	def before_delete(self):
		plantbot.dispatch_db_event('guild_removed', self)

	def before_insert(self):
		plantbot.dispatch_db_event('guild_joined', self)
