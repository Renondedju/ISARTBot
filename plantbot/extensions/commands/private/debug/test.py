import asyncio
import discord
import logging

from discord 	        import app_commands
from plantbot.bot       import PlantBot
from plantbot.extension import GroupExtension

class Test(GroupExtension, group_name="test"):

	bot   : PlantBot
	logger: logging.Logger
	
	def __init__(self, bot: PlantBot):
		self.bot    = bot
		self.logger = logging.getLogger(__name__)

	def check_test(interaction: discord.Interaction) -> bool:
		return interaction.user.id == 213262036069515264

	@app_commands.command()
	#@app_commands.check(check_test)
	async def test(self, interaction: discord.Interaction) -> None:
		"""A simple test command"""

		await self.bot.get_channel(1022584244473692231).create_thread(name="test", content="test", reason="test")
		await interaction.response.send_message("done.", ephemeral=True)

	@GroupExtension.db_listener()
	def on_database_ready(self) -> None:
		self.logger.info("Database ready")

async def setup(bot: PlantBot) -> None:
	# debug guild will always be set here since the extension is in a debug folder
	await bot.add_cog(Test(bot), guild=bot.debug_guild)