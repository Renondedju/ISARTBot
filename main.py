import os
import logging
import discord
import argparse

from plantbot.instance 			import plantbot
from plantbot.database.instance	import database
from plantbot.database.models   import *

def main():
	"""
		PlantBot setup and run

		Current working directory is set to the root of the project.

		Arguments:

			--debug-guild: The ID of the debug guild. If set, debug extensions will be loaded.
			--db_path: The path to the database file.
			--db_provider: The database provider.
			--log_file: The path to the log file.
			--safe_mode: If set, the bot will not load any extensions.

		Required environment variables:

			PLANTBOT_TOKEN: The bot token. (https://discord.com/developers/applications)
	"""

	# Set current working directory to the root of the project
	os.chdir(os.path.dirname(os.path.realpath(__file__)))

	# Logging exceptions for clarity
	logging.getLogger('discord.webhook.async_').setLevel(logging.INFO)
	logging.getLogger('discord.gateway')       .setLevel(logging.INFO)
	logging.getLogger('discord.client' )       .setLevel(logging.INFO)
	logging.getLogger('discord.http')          .setLevel(logging.INFO)

	# Parsing arguments
	parser = argparse.ArgumentParser(description="The plant discord bot 🌿")
	
	parser.add_argument("--db_path"    , type=str , default="database.sqlite", help="Path to the database file")
	parser.add_argument("--logging"    ,                                       help="Enables logging", action="store_true")
	parser.add_argument("--safe_mode"  ,                                       help="Disables all extensions", action="store_true")
	parser.add_argument("--log_file"   , type=str                            , help="Sets the log file path")
	parser.add_argument("--db_provider", type=str , default="sqlite"         , help="Database provider")
	parser.add_argument("--debug_guild", type=int , default=None             , help="Sets the debug guild ID and enables debug extensions")

	args   = parser.parse_args() 
	logger = logging.getLogger('plantbot')

	if args.log_file: discord.utils.setup_logging(handler=logging.FileHandler(filename=args.log_file, encoding='utf-8', mode='w+'))
	if args.logging:  discord.utils.setup_logging(handler=logging.StreamHandler())
	logging.root.setLevel(logging.DEBUG if args.debug_guild else logging.INFO)

	logger.info("------------------------- Plant Bot 🌿 -------------------------")
	if args.log_file: logger.info(f"Log file set to {args.log_file}")
	if (token := os.getenv("PLANTBOT_TOKEN")) is None:
		return logger.error("No token provided, please set the PLANTBOT_TOKEN environment variable")

	# Setup database and starting the bot
	database.bind(provider=args.db_provider, filename=args.db_path, create_db=True)
	database.generate_mapping(create_tables=True)
	plantbot.run(token = token,
		debug_guild = args.debug_guild,
		safe_mode   = args.safe_mode
	)

if __name__ == '__main__':
	main()