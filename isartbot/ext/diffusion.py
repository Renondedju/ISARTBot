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

from discord.ext       import commands
from isartbot.checks   import is_super_admin, is_moderator
from isartbot.database import Diffusion, DiffusionOperator, DiffusionSubscription

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

    @diffusion.group(pass_context=True, help="diffusion_operator_help", description="diffusion_operator_description")
    @commands.check(is_super_admin)
    async def operator(self, ctx):
        """ Diffusion operator command group """
        pass

    # Commands

    @diffusion.command(help="diffusion_create_help", description="diffusion_create_description")
    @commands.check(is_super_admin)
    async def create(self, ctx, diffusion_name: str):
        """ Creates a diffusion channel, this commands is reserved to super admins """

        # Checking if the diffusion already exists
        if (self.bot.database.session.query(Diffusion).filter(Diffusion.name == diffusion_name).first() != None):
            translations = await self.bot.get_translations(ctx, ["failure_title", "diffusion_already_exists"])
            embed = discord.Embed(
                title       = translations["failure_title"],
                description = translations["diffusion_already_exists"],
                color       = discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Otherwise, creating a new diffusion
        new_diffusion = Diffusion(name = diffusion_name)

        self.bot.database.session.add(new_diffusion)
        self.bot.database.session.commit()

        translations = await self.bot.get_translations(ctx, ["success_title", "diffusion_created"])
        embed = discord.Embed(
            title       = translations["success_title"],
            description = translations["diffusion_created"].format(diffusion_name),
            color       = discord.Color.green()
        )
        await ctx.send(embed=embed)

    @diffusion.command(help="diffusion_delete_help", description="diffusion_delete_description")
    @commands.check(is_super_admin)
    async def delete(self, ctx, diffusion_name: str):
        """ Deletes a diffusion channel, this commands is reserved to super admins """

        # Checking if the diffusion exists
        if (self.bot.database.session.query(Diffusion).filter(Diffusion.name == diffusion_name).first() == None):
            translations = await self.bot.get_translations(ctx, ["failure_title", "diffusion_doesnt_exists"])
            embed = discord.Embed(
                title       = translations["failure_title"],
                description = translations["diffusion_doesnt_exists"].format(diffusion_name, self.clean_prefix),
                color       = discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Otherwise, deleting the diffusion

        self.bot.database.session.query(Diffusion).\
            filter(Diffusion.name == diffusion_name).\
            delete()

        self.bot.database.session.commit()

        translations = await self.bot.get_translations(ctx, ["success_title", "diffusion_deleted"])
        embed = discord.Embed(
            title       = translations["success_title"],
            description = translations["diffusion_deleted"].format(diffusion_name),
            color       = discord.Color.green()
        )
        await ctx.send(embed=embed)

    @diffusion.command(help="diffusion_list_help", description="diffusion_list_description")
    async def list(self, ctx):
        """ Returns a lists of all the available diffusions """

        embed = discord.Embed()

        embed.title       = await ctx.bot.get_translation(ctx, 'diffusion_list_title')
        embed.description = '\n'.join([f"\u2022 {diffusion[0]}" for diffusion in ctx.bot.database.session.query(Diffusion.name).all()])
        embed.colour      = discord.Color.green()

        await ctx.send(embed=embed)

    @operator.command(help="diffusion_operator_add_help", description="diffusion_operator_add_description")
    async def add(self, ctx, diffusion_name: str, new_operator: discord.Member):
        """ Adds a new diffusion operator to the selected diffusion """
        pass

    @operator.command(help="diffusion_operator_remove_help", description="diffusion_operator_remove_description")
    async def remove(self, ctx, diffusion_name: str, old_operator: discord.Member):
        """ Removes a diffusion operator from the selected diffusion """
        pass

    @diffusion.command(help="diffusion_diffuse_help", description="diffusion_diffuse_description")
    async def diffuse(self, ctx, diffusion_name: str, message: discord.Message):
        """ Diffuses a messages to all subscribers """
        pass

    @diffusion.command(help="diffusion_subscribe_help", description="diffusion_subscribe_description")
    @commands.check(is_moderator)
    async def subscribe(self, ctx, diffusion_name: str, channel: discord.TextChannel, diffusion_tag: discord.Role = None):
        """ Subscribes to a diffusion """
        pass

    @diffusion.command(help="diffusion_unsubscribe_help", description="diffusion_unsubscribe_description")
    @commands.check(is_moderator)
    async def unsubscribe(self, ctx, diffusion_name: str):
        """ Unsubscribes off a diffusion """
        pass

def setup(bot):
    bot.add_cog(DiffusionExt(bot))