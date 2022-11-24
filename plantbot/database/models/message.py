import discord

from pony.orm     						   import Required, Optional, PrimaryKey, Set
from plantbot.instance		    		   import plantbot
from plantbot.database.instance 		   import database
from plantbot.database.models.text_channel import TextChannel

class Message(database.Entity):
	""" Discord message representation """
	
	def __init__(self, message: discord.Message, **kwargs):
		super().__init__(
			discord_id = message.id,
			channel    = TextChannel.get(discord_id=message.channel.id) 
					  or TextChannel(message.channel),
			**kwargs)

	discord_id = PrimaryKey(int, auto=False, size=64)
	
	# Relations
	channel    	   = Required(TextChannel     , reverse='messages')
	post           = Optional('GloryboardPost', reverse='post'   , cascade_delete=True)
	gloryboards    = Set     ('GloryboardPost', reverse='message', cascade_delete=True)
	reaction_roles = Set     ('ReactionRole'  , reverse='message', cascade_delete=True)

	def before_delete(self):
		plantbot.dispatch_db_event('message_removed', self)