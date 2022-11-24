import discord

from pony.orm     				           import Required
from plantbot.instance	    	           import plantbot
from plantbot.database.instance            import database
from plantbot.database.models.message      import Message
from plantbot.database.models.gloryboard   import Gloryboard
from plantbot.database.models.text_channel import TextChannel

class GloryboardPost(database.Entity):
	""" Gloryboard message representation """
	
	def __init__(self, /, message: discord.Message, post: discord.Message) -> None:

		# We need to be careful about forum channels, since posts are stored in threads and not in the forum channel itself
		channel        = post.channel if post.channel.type != discord.ChannelType.public_thread else post.channel.parent
		text_channel   = TextChannel.get(discord_id=channel.id) or TextChannel(channel)
		super().__init__(
			gloryboard = text_channel.gloryboard,
			message    = Message   .get(discord_id=message.id) or Message(message),
			post       = Message   .get(discord_id=post.id)    or Message(post),
		)

	gloryboard = Required(Gloryboard, reverse='posts')
	message    = Required(Message   , reverse='gloryboards')
	post       = Required(Message   , reverse='post')

	def before_delete(self):
		plantbot.dispatch_db_event('gloryboard_post_remove', self)