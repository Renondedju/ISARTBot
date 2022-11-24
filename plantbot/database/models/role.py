import discord

from pony.orm     				    import PrimaryKey, Required, Set
from plantbot.instance		        import plantbot
from plantbot.database.instance     import database
from plantbot.database.models.guild import Guild

class Role(database.Entity):
	"""
		Discord role representation
		This intermediate entity is used to automatically maintain roles in the database
		(ie. delete roles that no longer exists)
	"""

	def __init__(self, role: discord.Role, **kwargs):
		super().__init__(
			discord_id = role.id,
			guild      = Guild.get(discord_id=role.guild.id),
			**kwargs
		)

	discord_id     = PrimaryKey(int, auto=False, size=64)
	guild          = Required  (Guild, reverse="roles")

	# Relations
	reaction_roles = Set('ReactionRole', reverse='role', cascade_delete=True)

	def before_delete(self):
		plantbot.dispatch_db_event('guild_role_deleted', self)