# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018-2019 Renondedju

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

import discord

from discord.ext import commands

from isartbot.helper     import Helper
from isartbot.checks     import is_super_admin, is_moderator
from isartbot.database   import Diffusion, DiffusionOperator, DiffusionSubscription
from isartbot.converters import DiffusionConverter

class DiffusionExt(commands.Cog):
    """ Diffusion channels extension class """

    __slots__ = ("bot")

    def __init__(self, bot):

        self.bot = bot

    # Groups

    @commands.group(pass_context=True, help="diffusion_help", description="diffusion_description")
    async def diffusion(self, ctx):
        """ Diffusion command group """
        pass

    @diffusion.group(aliases = ["op"], pass_context=True, help="diffusion_operator_help", description="diffusion_operator_description")
    @commands.check(is_super_admin)
    async def operator(self, ctx):
        """ Diffusion operator command group """
        pass

    @diffusion.group(aliases = ["sub"], pass_context=True, help="diffusion_subscription_help", description="diffusion_subscription_description")
    @commands.check(is_moderator)
    async def subscription(self, ctx):
        """ Diffusion subscription command group """
        pass

    # Commands

    @diffusion.command(help="diffusion_create_help", description="diffusion_create_description")
    @commands.check(is_super_admin)
    async def create(self, ctx, diffusion_name: str):
        """ Creates a diffusion channel, this commands is reserved to super admins """

        # Checking if the diffusion already exists
        if (await DiffusionConverter().convert(ctx, diffusion_name) != None):
            return await self.diffusion_already_exists_error(ctx, diffusion_name)

        # Otherwise, creating a new diffusion
        new_diffusion = Diffusion(name = diffusion_name)

        self.bot.database.session.add(new_diffusion)
        self.bot.database.session.commit()

        await Helper.send_success(ctx, ctx.channel, "diffusion_created", format_content = (diffusion_name))

    @diffusion.command(help="diffusion_delete_help", description="diffusion_delete_description")
    @commands.check(is_super_admin)
    async def delete(self, ctx, diffusion: DiffusionConverter):
        """ Deletes a diffusion channel, this commands is reserved to super admins """

        # Checking if the diffusion exists
        if (diffusion == None):
            return await self.diffusion_does_not_exists_error(ctx)

        # Asking for confirmation
        result = await Helper.ask_confirmation(ctx, ctx.channel, "diffusion_delete_title",
            initial_content = "diffusion_delete_content", initial_format = (diffusion.name),
            success_content = "diffusion_deleted"       , success_format = (diffusion.name),
            failure_content = "diffusion_delete_aborted")
        if (not result):
            return

        # Otherwise, deleting the diffusion
        self.bot.database.session.delete(diffusion)
        self.bot.database.session.commit()

    @diffusion.command(name="list", help="diffusion_list_help", description="diffusion_list_description")
    async def diffusion_list(self, ctx):
        """ Returns a lists of all the available diffusions """

        embed = discord.Embed()

        embed.title       = await ctx.bot.get_translation(ctx, 'diffusion_list_title')
        embed.description = '\n'.join([f"\u2022 {diffusion[0]}" for diffusion in ctx.bot.database.session.query(Diffusion.name).all()])
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    @operator.command(help="diffusion_operator_add_help", description="diffusion_operator_add_description")
    async def add(self, ctx, diffusion: DiffusionConverter, new_operator: discord.Member):
        """ Adds a new diffusion operator to the selected diffusion """
        # Checking if the diffusion exists
        if (diffusion == None):
            return await self.diffusion_does_not_exists_error(ctx)

        # Checking if this member is already an operator
        operator = self.bot.database.session.query(DiffusionOperator.discord_id).\
            filter(DiffusionOperator.diffusion  == diffusion,
                   DiffusionOperator.discord_id == new_operator.id).count()

        if (operator > 0):
            return await self.member_is_already_operator(ctx, new_operator, diffusion.name)

        # Adding the new operator to the database
        self.bot.database.session.add(DiffusionOperator(diffusion = diffusion, discord_id = new_operator.id))
        self.bot.database.session.commit()

        await Helper.send_success(ctx, ctx.channel, "diffusion_operator_added", format_content = (new_operator.mention, diffusion.name))

    @operator.command(help="diffusion_operator_remove_help", description="diffusion_operator_remove_description")
    async def remove(self, ctx, diffusion: DiffusionConverter, old_operator: discord.Member):
        """ Removes a diffusion operator from the selected diffusion """

        # Checking if the diffusion exists
        if (diffusion == None):
            return await self.diffusion_does_not_exists_error(ctx)

        # Checking if this member is already an operator
        operator = self.bot.database.session.query(DiffusionOperator).\
            filter(DiffusionOperator.diffusion  == diffusion,
                   DiffusionOperator.discord_id == old_operator.id).first()

        if (operator == None):
            return await self.member_not_operator(ctx, old_operator, diffusion.name)

        # Asking for confirmation
        result = await Helper.ask_confirmation(ctx, ctx.channel, "diffusion_operator_remove_title",
            initial_content = "diffusion_operator_remove_content", initial_format = (old_operator.mention, diffusion.name),
            success_content = "diffusion_operator_removed"       , success_format = (old_operator.mention, diffusion.name),
            failure_content = "diffusion_operator_remove_content_failure")
        if (not result):
            return

        self.bot.database.session.delete(operator)
        self.bot.database.session.commit()

    @operator.command(name="list", help="diffusion_operator_list_help", description="diffusion_operator_list_description")
    async def operator_list(self, ctx, diffusion: DiffusionConverter):
        """ Lists all the current operators for a certain diffusion """

        # Checking if the diffusion exists
        if (diffusion == None):
            return await self.diffusion_does_not_exists_error(ctx)

        operators_id = self.bot.database.session.query(DiffusionOperator.discord_id).\
            filter(DiffusionOperator.diffusion == diffusion).all()

        embed = discord.Embed()

        embed.title       = (await ctx.bot.get_translation(ctx, 'diffusion_operator_list_title')).format(diffusion.name)
        embed.description = '\n'.join([f"\u2022 {(await self.bot.fetch_user(id[0])).mention}" for id in operators_id])
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    @diffusion.command(help="diffusion_diffuse_help", description="diffusion_diffuse_description")
    async def diffuse(self, ctx, diffusion: DiffusionConverter, *, message: str):
        """ Diffuses a messages to all subscribers """
        pass

    @subscription.command(aliases = ["sub", "add", "create"], help="diffusion_subscription_subscribe_help", 
        description="diffusion_subscription_subscribe_description")
    async def subscribe(self, ctx, diffusion: DiffusionConverter, channel: discord.TextChannel, diffusion_tag: discord.Role = None):
        """ Subscribes to a diffusion """
    
        # Checking if the diffusion exists
        if (diffusion == None):
            return await self.diffusion_does_not_exists_error(ctx)

        # Checking if the subscription for this channel already exists
        count = self.bot.database.session.query(DiffusionSubscription).\
            filter(DiffusionSubscription.diffusion          == diffusion,
                   DiffusionSubscription.discord_channel_id == channel.id).\
            count()
        
        if (count > 0):
            return await self.subscription_already_exists(ctx)

        # Checking if we have enough permissions in order to operate the starboard on the designated channel
        required_perms = discord.Permissions().none()
        required_perms.update(send_messages=True)
        if (not required_perms.is_subset(channel.permissions_for(ctx.guild.me))):
            raise commands.BotMissingPermissions(["send_messages"])

        new_subscription = DiffusionSubscription(
                discord_server_id  = ctx.guild.id,
                discord_channel_id = channel.id,
                tag                = diffusion_tag.mention if diffusion_tag != None else "",
                diffusion          = diffusion
            )

        self.bot.database.session.add(new_subscription)
        self.bot.database.session.commit()

        await Helper.send_success(ctx, ctx.channel, "diffusion_subscribe_success")

    @subscription.command(aliases = ["unsub", "remove", "delete"], help="diffusion_subscription_unsubscribe_help",
        description="diffusion_subscription_unsubscribe_description")
    async def unsubscribe(self, ctx, diffusion: DiffusionConverter, channel: discord.TextChannel):
        """ Unsubscribes off a diffusion """
        
        # Checking if the diffusion exists
        if (diffusion == None):
            return await self.diffusion_does_not_exists_error(ctx)

        subscription = self.bot.database.session.query(DiffusionSubscription).\
            filter(DiffusionSubscription.diffusion          == diffusion,
                   DiffusionSubscription.discord_channel_id == channel.id).\
            first()

        if (subscription == None):
            return await self.no_such_subscription_error(ctx)

        self.bot.database.session.delete(subscription)
        self.bot.database.session.commit()

        await Helper.send_success(ctx, ctx.channel, "diffusion_unsubscribe_success")

    @subscription.command(name = "list", help="diffusion_subscription_list_help", description="diffusion_subscription_list_description")
    async def subscription_list(self, ctx, channel: discord.TextChannel = None):
        """ Lists all the subscriptions in a channel or server """
        
        subscriptions = self.bot.database.session.query(DiffusionSubscription).\
            filter(DiffusionSubscription.discord_server_id == ctx.guild.id).\
            all()

        if len(subscriptions) > 0:
            descritpiton = '\n'.join([f"\u2022 {sub.diffusion.name} -> {(await self.bot.fetch_channel(sub.discord_channel_id)).mention}" for sub in subscriptions])
        else:
            descritpiton = await ctx.bot.get_translation(ctx, 'diffusion_subscription_list_empty')

        embed = discord.Embed()

        embed.title       = await ctx.bot.get_translation(ctx, 'diffusion_subscription_list_title')
        embed.description = descritpiton
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    # Error handlers

    async def diffusion_does_not_exists_error(self, ctx):
        """ Diffusion does not exists error """
        await Helper.send_error(ctx, ctx.channel, "diffusion_doesnt_exists", format_content = (ctx.prefix))

    async def diffusion_already_exists_error(self, ctx, diffusion_name: str):
        """ Diffusion already exists error """
        await Helper.send_error(ctx, ctx.channel, "diffusion_already_exists", format_content = (diffusion_name))

    async def member_is_already_operator(self, ctx, operator: discord.Member, diffusion_name: str):
        """ Member is already an operator error """
        await Helper.send_error(ctx, ctx.channel, "diffusion_already_operator", format_content = (operator.mention, diffusion_name))

    async def member_not_operator(self, ctx, member: discord.Member, diffusion_name: str):
        """ Member isn't an operator error """
        await Helper.send_error(ctx, ctx.channel, "diffusion_not_operator", format_content = (member.mention, diffusion_name))

    async def subscription_already_exists(self, ctx):
        """ Subscription already exists error """
        await Helper.send_error(ctx, ctx.channel, "diffusion_subscription_already_exists", format_content = (ctx.prefix))

    async def no_such_subscription_error(self, ctx):
        """ No such subscription error """
        await Helper.send_error(ctx, ctx.channel, "diffusion_no_such_subscription", format_content = (ctx.prefix))


def setup(bot):
    bot.add_cog(DiffusionExt(bot))