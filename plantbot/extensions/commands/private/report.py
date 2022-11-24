from enum import Enum
import discord
import logging

from plantbot.bot    	      import PlantBot
from plantbot.database.models import *
from plantbot.guilds 		  import isart_student_guild
from discord 	              import app_commands
from discord.ext              import commands

class Report(commands.Cog):
	""" Report to Server Mods/ISART's Ethic Team context menus """

	def __init__(self, bot: PlantBot):
		
		self.bot         = bot
		self.logger      = logging.getLogger(__name__)

		self.ctx_report_mods = app_commands.ContextMenu(
			name     = "Report (Moderators)",
			callback = self.report_mods 
		)
		self.ctx_report_ethic = app_commands.ContextMenu(
			name     = "Report (Éthique)",
			callback = self.report_ethic 
		)

		self.bot.tree.add_command(self.ctx_report_mods)
		self.bot.tree.add_command(self.ctx_report_ethic)

	@app_commands.guilds(isart_student_guild.id)
	async def report_mods(self, interaction: discord.Interaction, message: discord.Message):
		await interaction.response.send_modal(ReportModal(self.bot, message, ReportTeam.Moderators))

	@app_commands.guilds(isart_student_guild.id)
	async def report_ethic(self, interaction: discord.Interaction, message: discord.Message):
		await interaction.response.send_modal(ReportModal(self.bot, message, ReportTeam.Ethic))

	async def cog_unload(self) -> None:
		self.bot.tree.remove_command(self.ctx_report_mods.name , type=self.ctx_report_mods.type)
		self.bot.tree.remove_command(self.ctx_report_ethic.name, type=self.ctx_report_ethic.type)

class ReportTeam(Enum):
	Moderators = 0
	Ethic      = 1

class ReportModal(discord.ui.Modal, title='Report Message'):
	""" Report Modal Component """

	# -------- Modal Contents
	feedback = discord.ui.TextInput(
		style       = discord.TextStyle.paragraph,
		label       = 'Reason',
		placeholder = 'A clear and concise description of what the problem is.',
		max_length  = 1024)

	name = discord.ui.TextInput(
		label       = 'Name',
		placeholder = "Leave blank to remain anonymous",
		required    = False)
	# --------

	def __init__(self, bot: PlantBot, message: discord.Message, team: ReportTeam):
		self.bot     = bot
		self.team    = team
		self.message = message

		super().__init__()

	def get_reporter_name(self, interaction: discord.Interaction) -> str:
		""" Returns the name of the reporter """
		return f"{self.name.value} - {interaction.user.name}#{interaction.user.discriminator}" if self.name.value else 'Anonymous'

	async def send_report(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
		""" Sends a report to the given channel """

		embed = discord.Embed(title='Reported Message')
		if self.message.content:
			embed.description = self.message.content

		embed.set_author(name=self.message.author.display_name, icon_url=self.message.author.display_avatar.url)
		embed.add_field (name='Reason', value=self.feedback.value, inline=True)
		embed.add_field (name='Author', value=self.get_reporter_name(interaction), inline=True)
		embed.timestamp = self.message.created_at

		url_view = discord.ui.View()
		url_view.add_item(discord.ui.Button(label='Go to message', style=discord.ButtonStyle.url, url=self.message.jump_url))

		await channel.send(embed=embed, view=url_view)

	async def send_response(self, interaction: discord.Interaction) -> None:
		view = discord.ui.View()

		await interaction.response.send_message(f'The message has been reported!', view=view, ephemeral=True)

	async def on_submit(self, interaction: discord.Interaction):

		log_channel = (self.bot.get_channel(459018827703910430)
			if self.team == ReportTeam.Moderators else
			self.bot.get_channel(459018827703910430))

		await self.send_report(interaction, log_channel)
		await self.send_response(interaction)

	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
		await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
		logging.getLogger(__name__).exception(error)

async def setup(bot: PlantBot) -> None:
	await bot.add_cog(Report(bot))