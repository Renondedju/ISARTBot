# MIT License

# Copyright (c) 2018-2020 Renondedju

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from discord.ext         import commands
from discord.utils 	     import get
from isartbot.checks     import is_admin
from isartbot.database   import Server
from isartbot.converters import BetterRoleConverter

class VerificationExt(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@commands.group(name="verification", invoke_without_command=True)
	@commands.check(is_admin)
	async def verification(self, ctx):
		""" Verification management commands """
		
		# Prints out the current verified role
		if ctx.invoked_subcommand is None:
			server = self.bot.database.session.query(Server).filter(Server.discord_id == ctx.guild.id).first()
			if server.verified_role_id == 0:
				await ctx.send("No verified role set")
			else:
				verified_role = get(ctx.guild.roles, id=server.verified_role_id)
				await ctx.send(f"Verified role is {verified_role.mention}")

	@verification.command(name="set")
	@commands.check(is_admin)
	async def verification_set(self, ctx, role: BetterRoleConverter):
		""" Sets the verified role for this guild in the database """
		
		server = self.bot.database.session.query(Server).filter(Server.discord_id == ctx.guild.id).first()
		server.verified_role_id = role.id
		self.bot.database.session.commit()

		await ctx.send(f"Verified role set to {role.mention}")

	@verification.command(name="disable")
	@commands.check(is_admin)
	async def verification_disable(self, ctx):
		""" Disables the verification system for this guild """
		
		server = self.bot.database.session.query(Server).filter(Server.discord_id == ctx.guild.id).first()
		server.verified_role_id = 0
		self.bot.database.session.commit()

		await ctx.send("Verification system disabled")

def setup(bot):
    bot.add_cog(VerificationExt(bot))