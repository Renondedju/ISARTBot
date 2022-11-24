import discord

from pony.orm     				           import Required, Set, PrimaryKey
from plantbot.instance	    	           import plantbot
from plantbot.database.instance            import database
from plantbot.database.models.text_channel import TextChannel
from plantbot.database.models.guild        import Guild

class Gloryboard(database.Entity):

	def __init__(self, channel: discord.TextChannel, **kwargs) -> None:
		super().__init__(
			channel = TextChannel.get(discord_id=channel.id) or TextChannel(channel)
			**kwargs
		)

	channel = PrimaryKey(TextChannel, reverse='gloryboard')
	emoji   = Required  (str, default = '⭐')
	minimum = Required  (int, default = 3)
	color   = Required  (int, default = 0xFEE75C)
	
	# Relationships
	posts   = Set('GloryboardPost', reverse='gloryboard', cascade_delete=True)

	def before_insert(self):
		plantbot.dispatch_db_event('gloryboard_added', self)

	def before_delete(self):
		plantbot.dispatch_db_event('gloryboard_removed', self)