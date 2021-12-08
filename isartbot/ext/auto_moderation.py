import discord

from discord.ext          import commands
from discord.ext.commands import Cog
from isartbot.database    import Server, AutoModerableChannel

class AutoModerationExt(Cog):

    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()

    @commands.group(invoke_without_command=True, pass_context=True)
    @commands.bot_has_permissions(manage_messages = True)
    @commands.has_permissions    (manage_messages = True)
    async def am(self, ctx):
        await ctx.send_help(ctx.command)

    # Commands that adds an auto moderable channel
    @am.command(name='add', pass_context=True)
    @commands.bot_has_permissions(manage_messages = True)
    @commands.has_permissions    (manage_messages = True)
    async def am_add(self, ctx, channel: discord.TextChannel):

        server = self.bot.database.session.query(Server).filter(Server.discord_id == ctx.guild.id).first()

        am_channel = AutoModerableChannel(
            discord_id = channel.id,
            server     = server
        )

        self.bot.database.session.add(am_channel)
        self.bot.database.session.commit()

        await ctx.send(f'{channel.mention} is now auto moderated.')
    
    # Commands that removes an auto moderable channel
    @am.command(name='remove', pass_context=True)
    @commands.bot_has_permissions(manage_messages = True)
    @commands.has_permissions    (manage_messages = True)
    async def am_remove(self, ctx, channel: discord.TextChannel):
            
        am_channel = self.bot.database.session.query(AutoModerableChannel).filter(AutoModerableChannel.discord_id == channel.id).first()

        self.bot.database.session.delete(am_channel)
        self.bot.database.session.commit()

        await ctx.send(f'{channel.mention} is no longer auto moderated.')

    # --- Events ---

    @Cog.listener()
    async def on_reaction_add(self, reaction, user):

        # Checks if the reaction is a 🗑️ emoji
        if reaction.emoji != '🗑️':
            return

        # Fetching auto moderable channels from database
        am_channels        = list(self.bot.database.session.query(AutoModerableChannel).all())
        am_server_channels = [channel for channel in am_channels if channel.server.discord_id == reaction.message.guild.id]

        # Checks if the channel is auto moderable
        if reaction.message.channel.id not in [channel.discord_id for channel in am_server_channels]:
            return

        # Deleting the message
        await reaction.message.delete()

def setup(bot) -> None:
    bot.add_cog(AutoModerationExt(bot))