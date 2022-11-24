from pony.orm     				      import Required
from plantbot.instance		          import plantbot
from plantbot.database.instance       import database
from plantbot.database.models.role    import Role
from plantbot.database.models.message import Message

class ReactionRole(database.Entity):
	"""
		Self assignable role interaction representation
		Used by the commands.global.roles extension 
	"""

	message = Required(Message, reverse="reaction_roles")
	role    = Required(Role   , reverse="reaction_roles")
	emoji   = Required(str)

	def before_delete(self):
		plantbot.dispatch_db_event('role_interaction_removed', self)
		