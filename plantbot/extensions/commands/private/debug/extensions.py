import asyncio
import discord
import logging

from enum            import Enum
from typing          import List, Optional
from plantbot.bot    import PlantBot
from discord 	     import app_commands
from discord.ext     import commands

class ManageAction(Enum):
	Load   = "\U0001f4be Load" # Floppy disk emoji
	Unload = "\U0001f4bf Unload" # Floppy disk emoji
	Reload = "\U0001f504 Reload" # Clockwise vertical arrows emoji

class Extensions(commands.GroupCog, group_name='extensions'):
	"""Extension manager"""

	bot   : PlantBot
	logger: logging.Logger

	def __init__(self, bot: PlantBot):
		self.bot    = bot
		self.logger = logging.getLogger(__name__)

	@app_commands.command()
	async def list(self, interaction: discord.Interaction) -> None:
		"""Lists all the currently loaded extensions"""

		loaded_emoji   = discord.PartialEmoji(name='\N{LARGE GREEN CIRCLE}')
		unloaded_emoji = discord.PartialEmoji(name='\N{LARGE RED CIRCLE}')

		await interaction.response.send_message(embed = discord.Embed(
			title       = "Extension List",
			color       = discord.Color.green(),
			description = '\n'.join([f"{loaded_emoji if extension.loaded else unloaded_emoji} - {extension}" for extension in self.bot.get_extension_list()]) or "None"
		), ephemeral=True)

	@app_commands.command()
	async def sync(self, interaction: discord.Interaction, guild: Optional[str]) -> None:
		""" Syncs the command tree for the passed guild. Syncs the global tree if no guild is passed """

		await interaction.response.defer(ephemeral=True, thinking=True)

		try:
			if guild is None:
				await self.bot.tree.sync()
				await interaction.followup.send("Synced the global command tree", ephemeral=True)
			elif guild.lower() == "debug":
				if self.bot.debug_guild is None:
					await interaction.followup.send("No debug guild set", ephemeral=True)
				else:
					await self.bot.sync_tree()
				await interaction.followup.send(f"Synced the command tree for the debug guild", ephemeral=True)
			else:
				await self.bot.tree.sync(guild=discord.Object(id=guild))
				await interaction.followup.send(f"Synced the command tree for id={guild}", ephemeral=True)
		except Exception as e:
			await interaction.followup.send(f"Failed to sync the command tree: {e}", ephemeral=True)

	@app_commands.command()
	@app_commands.describe(wildcard="Wildcard of all the extensions to manage", action="Action to perform on the extension")
	async def manage(self, interaction: discord.Interaction, wildcard: str, action: ManageAction) -> None:
		"""Manages the extensions"""

		await interaction.response.defer(ephemeral=True, thinking=True)

		if action == ManageAction.Load:
			await self.execute(interaction, wildcard, self.bot.load_extension, "load")
		elif action == ManageAction.Unload:
			await self.execute(interaction, wildcard, self.bot.unload_extension, "unload")
		elif action == ManageAction.Reload:
			await self.execute(interaction, wildcard, self.bot.reload_extension, "reload")

	async def execute(self, interaction: discord.Interaction, wildcard: str, func: callable, verb: str) -> None:
		"""Executes a function on extensions"""

		extensions = [extension for extension in self.bot.get_extension_list(wildcard)]
		success    = await asyncio.gather(*(func(extension.identifier) for extension in extensions))
		
		if not extensions:
			await interaction.followup.send(embed = discord.Embed(
				title       = "Extensions not found",
				color       = discord.Color.red(),
				description = f"The wildcard `{wildcard}` didn't match any extensions"
			), ephemeral=True)
		elif all(success):
			text = '\n'.join([f"• `{ext.identifier}`" for ext in extensions])
			await interaction.followup.send(embed = discord.Embed(
				title       = f"Extension {verb}ed" if len(extensions) == 1 else f"Extensions {verb}ed",
				color       = discord.Color.green(),
				description = f"The following extension{'s' if len(extensions) > 1 else ''} have been {verb}ed:\n{text}"
			), ephemeral=True)
		else:
			failed    = [ext.name for ext, success in zip(extensions, success) if not success]
			succeeded = [ext.name for ext, success in zip(extensions, success) if success]
			embed     = discord.Embed(
				title       = f"Extension failed to {verb}" if len(failed) == 1 else f"Some extensions failed to {verb}",
				color       = discord.Color.red(),
				description = '\n'.join([f"\U0001f534 {fail}"    for fail    in failed]) + "\n"
						    + '\n'.join([f"\U0001f7e2 {success}" for success in succeeded]),
			)
			embed.set_footer(text=f"Check logs for more information")
			await interaction.followup.send(embed = embed, ephemeral=True)

	@manage.autocomplete('wildcard')
	async def autocomplete_extension(self, _: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
		"""Auto completes an extension"""

		condition  = lambda extension: (current == "") or (current in extension.name)
		extensions = [extension for extension in self.bot.get_extension_list() if condition(extension)]

		values = [discord.app_commands.Choice(
			name  = str(extension),
			value = extension.identifier) for extension in extensions]

		values.extend(set(discord.app_commands.Choice(
			name  = f"{'.'.join(extension.name      .split('.')[:-1])}.*",
			value = f"{'.'.join(extension.identifier.split('.')[:-1])}.*") for extension in extensions))

		values.sort(key=lambda choice: (len(choice.name), choice.name))
		return values[:25]

async def setup(bot: PlantBot):
	#guilds = [isart_student_guild] if (bot.debug_guild is None) else [bot.debug_guild, isart_student_guild]
	await bot.add_cog(Extensions(bot), guild=bot.debug_guild)