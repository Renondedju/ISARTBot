import time

from typing               import Union
from discord              import *
from discord.ext.commands import Cog
from plantbot.bot         import PlantBot
from plantbot.extension   import Extension
from plantbot.database    import models

class DatabaseExtension(Extension):
	"""
		Automatically listens for channels/roles/guilds that are
		added/removed in order to maintain the database

		Catchups are also performed when the extension is loaded
	"""
	
	@Extension.listener()
	async def on_database_sync(self) -> None:
		"""Synchs the database with the current state of the bot"""

		start = time.time()

		# Removing guilds that should no longer be tracked
		with models.db_session:
			
			for guild in models.Guild.select():
				if guild.discord_id not in [g.id for g in self.bot.guilds]:
					guild.delete()

		for guild in self.bot.guilds:

			with models.db_session:
				if not models.Guild.exists(discord_id=guild.id):
					models.Guild(guild)

				# Otherwise check for deleted channels or roles
				else:

					# Check for deleted channels
					for channel in models.TextChannel.select(lambda c: c.guild.discord_id == guild.id):
						for discord_channel in guild.channels:
							if channel.discord_id == discord_channel.id:
								channel.is_forum = discord_channel.type == ChannelType.forum
								break
						else:
							channel.delete()

					# Check for deleted roles
					for role in models.Role.select(lambda r: r.guild.discord_id == guild.id):
						if role.discord_id not in [r.id for r in guild.roles]:
							role.delete()

		# Log the time it took to sync the database in milliseconds
		self.logger.info(f"Synced database in {round((time.time() - start) * 1000)}ms")

	# Guild events
	@Extension.listener()
	async def on_guild_join(self, guild: Guild) -> None:
		""" Adds the corresponding guild to database """

		with models.db_session:
			models.Guild(guild)

	@Extension.listener()
	async def on_guild_remove(self, guild: Guild) -> None:
		""" Removes the corresponding guild from database """

		with models.db_session:
			models.Guild.select(discord_id=guild.id).delete()

	@Extension.db_listener()
	def db_guild_joined(self, guild: models.Guild) -> None:
		self.logger.info(f"Added guild {guild.discord_id} to database")

	@Extension.db_listener()
	def db_guild_removed(self, guild: models.Guild) -> None:
		self.logger.info(f"Removed guild {guild.discord_id} from database")

	# Channels events
	@Extension.listener()
	async def on_guild_channel_delete(self, channel: TextChannel) -> None:
		""" Removes the corresponding channel from database """

		with models.db_session:
			models.TextChannel.select(discord_id=channel.id).delete()
	
	@Extension.listener()
	async def on_guild_channel_update(self, before: Union[TextChannel, ForumChannel], after: Union[TextChannel, ForumChannel]) -> None:
		""" Updates the corresponding channel in database """

		with models.db_session:
			if (channel := models.TextChannel.get(discord_id=after.id)):
				channel.is_forum = after.type == ChannelType.forum

	@Extension.listener()
	async def on_raw_thread_delete(self, payload: RawThreadDeleteEvent) -> None:
		""" Removes the corresponding thread (aka text channel) from database """

		with models.db_session:
			models.TextChannel.select(discord_id=payload.thread_id).delete()

	@Extension.db_listener()
	def db_text_channel_removed(self, channel: models.TextChannel) -> None:
		self.logger.debug(f"Removed channel {channel.discord_id} from database")

	# Role events
	@Extension.listener()
	async def on_role_remove(self, role: Role) -> None:
		""" Removes the corresponding role from database """

		with models.db_session:
			models.Role.select(discord_id=role.id).delete()

	@Extension.db_listener()
	def db_role_removed(self, role: models.Role) -> None:
		self.logger.info(f"Removed role {role.discord_id} from database")

	# Message events
	@Cog.listener()
	async def on_raw_message_delete(self, payload: RawMessageDeleteEvent) -> None:
		"""Called when a message is deleted"""

		# Remove the message from the database
		with models.db_session:
			models.Message.select(discord_id=payload.message_id).delete()

	@Cog.listener()
	async def on_raw_bulk_message_delete(self, payload: RawBulkMessageDeleteEvent) -> None:
		"""Called when a bulk of messages are deleted"""

		# Remove the messages from the database
		with models.db_session:
			models.Message.select(lambda m: m.discord_id in payload.message_ids).delete()

	@Extension.db_listener()
	def db_message_removed(self, message: models.Message) -> None:
			self.logger.debug(f"Removed message {message.discord_id} from database")

async def setup(bot: PlantBot):
	""" Adds the extension to the bot """
	
	await bot.add_cog(DatabaseExtension(bot))