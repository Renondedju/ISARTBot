import discord

from typing                         import Union
from pony.orm          				import PrimaryKey, Required, Optional, Set
from plantbot.database.instance     import database
from plantbot.instance 				import plantbot
from plantbot.database.models.guild import Guild

class TextChannel(database.Entity):
	"""
		Discord text channel representation
		This intermediate entity is used to automatically maintain text channels in the database
		(ie. delete channels that no longer exists)
	"""

	def __init__(self, channel: Union[discord.TextChannel, discord.ForumChannel, discord.Thread], **kwargs):
		super().__init__(
			discord_id = channel.id,
			guild      = Guild.get(discord_id=channel.guild.id),
			is_forum   = channel.type == discord.ChannelType.forum or 
						 channel.type == discord.ChannelType.public_thread and channel.parent.type == discord.ChannelType.forum,
			**kwargs
		)

	discord_id = PrimaryKey(int, auto=False, size=64)
	guild      = Required(Guild, reverse="text_channels")
	is_forum   = Optional(bool , default=False)

	# Relations
	gloryboard = Optional('Gloryboard', reverse='channel', cascade_delete=True)
	messages   = Set     ('Message'   , reverse='channel', cascade_delete=True)

	def before_delete(self):
		plantbot.dispatch_db_event('text_channel_removed', self)
