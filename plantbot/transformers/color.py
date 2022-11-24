import re
import discord

from typing import List

class ColorTransformer(discord.app_commands.Transformer):

	regex: str = re.compile(r"^\s*((?:0x)?#?)?([\da-fA-F]{0,6})\s*$")

	async def autocomplete(self, interaction: discord.Interaction, value: str, /) -> List[str]:

		if (matches := re.match(self.regex, value)) is None:
			return []

		color = int(matches.group(2) or '0', base=16)
		value =  f"{matches.group(1)}{color:0<6X}"

		return [discord.app_commands.Choice(name=value, value=value)]

	async def transform(self, interaction: discord.Interaction, value: str) -> discord.Color:

		if (matches := re.match(self.regex, value)) is None:
			return None #TODO: Raise error

		color = int(matches.group(2) or '0', base=16)
		return discord.Color(color)