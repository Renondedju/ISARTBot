import re
import asyncio
import weakref
import discord

import emoji as emoji_package

from typing 		          import List, NamedTuple, Union
from discord 	              import app_commands
from plantbot.bot             import PlantBot
from plantbot.transformers    import ColorTransformer
from plantbot.extension       import GroupExtension
from plantbot.database        import models

class PostContent(NamedTuple):
	""" Represents the content of a post """

	title: str
	message: dict

@app_commands.guild_only()
@app_commands.default_permissions(manage_channels=True)
class GloryBoard(GroupExtension, group_name='gloryboard'):
	""" With enough reactions, a message will be copied to the gloryboard in a nicely formatted embed. """
	# The reaction emoji has traditionally been the star emoji, but it can be changed
	# as well as the minimum amount of reactions needed to post to the gloryboard.

	locks : weakref.WeakValueDictionary[int, asyncio.Lock] = weakref.WeakValueDictionary()

	image_regex   = re.compile(r"(https?:\/\/.*\.(?:png|jpg|jpeg|gif|webp|png|svg|bmp))")
	content_regex = re.compile(r"(https?:\/\/.*\.(?:[a-zA-Z]+))")

	## --------- Gloryboard commands --------- ##

	@app_commands.command()
	@app_commands.describe(
		channel = "The channel to enable the gloryboard in",
		emoji   = "The emoji to track reactions with",
		minimum = "The minimum amount of reactions needed to post to the gloryboard",
		color   = "The color of the embeds on the gloryboard, in hexadecimal (#00FF00)")
	async def set(self,
		interaction: discord.Interaction,
		channel    : Union[discord.TextChannel, discord.ForumChannel],
		minimum    : app_commands.Range[int, 1, 1000] = 0,
		emoji      : str = '',
		color      : app_commands.Transform[discord.Color, ColorTransformer] = None) -> None:
		""" Sets or updates the gloryboard settings for the current guild """
		
		emoji = emoji.strip()

		if not emoji_package.emoji_count(emoji) == 1 and (not emoji == ''):
			await interaction.response.send_message("Invalid emoji", ephemeral=True)
			return

		with models.db_session:
			# Getting or creating a new gloryboard

			channel_model = models.TextChannel.get(discord_id=channel.id) or models.TextChannel(channel)
			gloryboard    = models.Gloryboard .get(channel=channel_model) or models.Gloryboard (channel)

			emoji = emoji or gloryboard.emoji
			color = int(color or gloryboard.color)
			minimum = minimum  or gloryboard.minimum

			gloryboard.emoji   = emoji
			gloryboard.minimum = minimum
			gloryboard.color   = color

		# \U0001f44c = ok hand emoji
		await interaction.response.send_message(embed=discord.Embed(
			title       = "Gloryboard updated ! \U0001f44c", 
			color       = color,
			description = f"The bot will now post messages with __{minimum} or more {emoji}__ reactions to {channel.mention} with the same color as this embed."
		), ephemeral=True)

	@app_commands.command()
	@app_commands.describe(channel = "The channel to disable the gloryboard in")
	async def disable(self, interaction: discord.Interaction, channel: Union[discord.TextChannel, discord.ForumChannel]) -> None:
		""" Disables the gloryboard for the current guild """
		
		with models.db_session:
			channel_model   = models.TextChannel.get(discord_id=channel.id) or models.TextChannel(channel)
			if (gloryboard := models.Gloryboard .get(channel=channel_model)):
				gloryboard.delete()

		await interaction.response.send_message(f"Gloryboard disabled in {channel.mention}", ephemeral=True)

	## --------- Gloryboard logic --------- ##

	def count_reactions(self, message: discord.Message, emoji: str) -> int:
		""" Counts the amount of reactions on a message with a specific emoji """

		for reaction in message.reactions:
			if reaction.emoji == emoji:
				return reaction.count
		
		return 0

	def get_image_urls(self, message: discord.Message) -> List[str]:
		""" Returns a list of image urls from a message """

		content_matches    = self.image_regex.findall(message.content)
		attachment_matches = [ ]
		for attachment in message.attachments:
			match = self.image_regex.match(attachment.url)
			if match:
				attachment_matches.append(match.group(0))
		

		# Iterating over the matches by priority
		return [match for match in set(attachment_matches + content_matches)]

	def get_content_urls(self, message: discord.Message) -> List[str]:
		""" Returns a list of image urls from a message """

		content_matches    = self.content_regex.findall(message.content)
		attachment_matches = [ ]
		for attachment in message.attachments:
			match = self.content_regex.match(attachment.url)
			if match:
				attachment_matches.append(match.group(0))

		# Iterating over the matches by priority
		return [match for match in set(attachment_matches + content_matches)]

	def create_gloryboard_post(self, message: discord.Message, emoji: str, count: int, color: discord.Color) -> PostContent:
		""" Creates a gloryboard post from a message """

		images  = self.get_image_urls(message)
		content = self.get_content_urls(message)
		all     = set(images + content)
		view    = discord.ui.View()
		view.add_item(discord.ui.Button(label="Go to message", url=message.jump_url))

		# Remove the first link in the content of the message 
		message_content = message.content.replace(images[0], '', 1) if content else message.content

		embed = discord.Embed(description=f"{emoji} **{count}**\n\n{message_content}", color=color)
		embed.set_author(name=f"{message.author.display_name}", icon_url=message.author.avatar.url, url=message.jump_url)

		if images:
			embed.set_image(url=images[0] if images else None)
			all.remove(images[0])

		if len(content) > len(images):
			embed.add_field(name="Attachments", value="\n".join(set(content).difference(images)), inline=False)
		
		return PostContent(message_content[:25] or emoji, {"embed": embed, "content": "", "view": view})

	async def process_raw_reaction_event(self, payload: Union[discord.RawReactionActionEvent, discord.RawReactionClearEmojiEvent]) -> None:
		""" Processes a single reaction addition or removal """

		channel = self.bot     .get_channel  (payload.channel_id)
		message = await channel.fetch_message(payload.message_id)
		allowed_message_types = (
			discord.MessageType.default,
			discord.MessageType.reply,
			discord.MessageType.thread_starter_message,
			discord.MessageType.thread_created)

		# Don't process any reactions on bot messages, news channels or non conventional message types
		if channel.is_news() or not (message.type in allowed_message_types) or message.author.bot:
			return

		# If a gloryboard is set in the channel and the emoji is the right one
		with models.db_session:
			gloryboard = models.Gloryboard.get(lambda g: (g.emoji == payload.emoji.name and g.channel.guild.discord_id == payload.guild_id))

		if gloryboard:
			await self.process_reactions(message, gloryboard)

	async def process_reactions(self, original: discord.Message, gloryboard: models.Gloryboard) -> None:
		""" Processes the reactions on a message and does the necessary actions """

		# This function is only called when the proper emoji is added to a message
		# so we can safely lock on that message id
		async with self.locks.setdefault(original.id, asyncio.Lock()):

			# Checking if the message is already in the gloryboard
			with models.db_session:
				entry = models.GloryboardPost.get(
					message    = models.Message   .get(discord_id = original.id) or models.Message(original),
					gloryboard = models.Gloryboard.get(lambda g: g.emoji==gloryboard.emoji)
				) 
				post_channel = self.bot.get_channel(entry.post.channel.discord_id) if entry else None

			# If the message is already in the gloryboard, edit it
			if entry:			
				if self.bot.get_channel(gloryboard.channel.discord_id).type == discord.ChannelType.forum:
					await self.update_forum_post(original, entry, gloryboard, post_channel)
				else:
					await self.update_text_post(original, entry, gloryboard, post_channel)

			# Otherwise, create a new post
			else:
				if self.bot.get_channel(gloryboard.channel.discord_id).type == discord.ChannelType.forum:
					await self.create_forum_post(original, gloryboard)
				else:
					await self.create_text_post(original, gloryboard)

	async def update_forum_post(self, original: discord.Message, entry: models.GloryboardPost, gloryboard: models.Gloryboard, post_channel: discord.Thread) -> None:
		""" Updates a forum post """

		post                = await post_channel.fetch_message(entry.post.discord_id)
		reaction_count      = self.count_reactions(original, gloryboard.emoji)
		post_has_messages   = post.id != post_channel.last_message_id
		post_has_reactions  = bool(post.reactions)

		# post_has_messages is true if the thread has been written to, even if the messages have
		# been deleted since. Since the case isn't super likely to happen, we'll just ignore it to
		# avoid another api call and process things a bit quicker.

		if not post_has_messages and not post_has_reactions and reaction_count < gloryboard.minimum:
			await post_channel.delete()

		else:
			post_content = self.create_gloryboard_post(original, gloryboard.emoji, reaction_count, discord.Color(gloryboard.color))
			await post.edit(**post_content.message)

	async def update_text_post(self, original: discord.Message, entry: models.GloryboardPost, gloryboard: models.Gloryboard, post_channel: discord.TextChannel) -> None:
		""" Updates a text post """

		post           = await post_channel.fetch_message(entry.post.discord_id)
		reaction_count = self.count_reactions(original, gloryboard.emoji)

		if reaction_count >= gloryboard.minimum:
			post_content = self.create_gloryboard_post(original, gloryboard.emoji, reaction_count, discord.Color(gloryboard.color))
			await post.edit(**post_content.message)
		else:
			await post.delete()

	async def create_forum_post(self, original: discord.Message, gloryboard: models.Gloryboard) -> None:
		""" Creates a forum post """

		if (reaction_count := self.count_reactions(original, gloryboard.emoji)) < gloryboard.minimum:
			return

		post_channel   = self.bot.get_channel(gloryboard.channel.discord_id)
		post_content   = self.create_gloryboard_post(original, gloryboard.emoji, reaction_count, discord.Color(gloryboard.color))
		thread         = await post_channel.create_thread(name=post_content.title, **post_content.message)

		with models.db_session:
			models.GloryboardPost(message=original, post=thread.message)

	async def create_text_post(self, original: discord.Message, gloryboard: models.Gloryboard) -> None:
		""" Creates a text post """

		if (reaction_count := self.count_reactions(original, gloryboard.emoji)) < gloryboard.minimum:
			return

		post_channel   = self.bot.get_channel(gloryboard.channel.discord_id)
		post_content   = self.create_gloryboard_post(original, gloryboard.emoji, reaction_count, discord.Color(gloryboard.color))
		post           = await post_channel.send(**post_content.message)

		with models.db_session:
			models.GloryboardPost(message=original, post=post)

	# --- Event handlers

	@GroupExtension.db_listener()
	def db_gloryboard_post_remove(self, post: models.GloryboardPost) -> None:
		""" Called when a message is deleted from the database, either from a manual deletion or a cascade delete """

		async def cleanup_post(channel_id: int, post_id: int) -> None:
			try:
				channel = await self.bot.fetch_channel(channel_id)

				# Deleting empty threads (channel.id == id of the thread starter message)
				if channel and channel.type == discord.ChannelType.public_thread and channel.id == channel.last_message_id:
					await channel.delete()

				elif channel and (post := await channel.fetch_message(post_id)):
					await post.delete()

			except discord.NotFound:
				pass

		# If a gloryboard is removed, it could be because one of the two messages (original/post) was deleted, or the 
		# reaction count dropped below the minimum. In either case, delete the post on discord to reflect the changes
		self.bot.loop.create_task(cleanup_post(post.post.channel.discord_id, post.post.discord_id))

	@GroupExtension.listener()
	async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
		""" Called when a reaction is added to a message """

		# Ignore bot reactions
		if payload.member.bot:
			return

		await self.process_raw_reaction_event(payload)

	@GroupExtension.listener()
	async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
		""" Called when a reaction is removed from a message """
		await self.process_raw_reaction_event(payload)

	@GroupExtension.listener()
	async def on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent) -> None:
		""" Called when all reactions are removed from a message """
		
		with models.db_session:
			message = models.Message.get(discord_id=payload.message_id)
			if message and (post := models.GloryboardPost.get(message=message)):
				post.delete()

async def setup(bot: PlantBot) -> None:
	await bot.add_cog(GloryBoard(bot))