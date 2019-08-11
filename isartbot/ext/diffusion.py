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

from discord.ext     import commands
from discord.ext.commands     import command
from isartbot.checks import is_super_admin, is_moderator

class DiffusionExt(commands.Cog):
    """ Diffusion channels extension class """

    __slots__ = ("bot")

    def __init__(self, bot):

        self.bot = bot

    @commands.group(pass_context=True, help="diffusion_help", description="diffusion_description")
    async def diffusion(self, ctx):
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

        pass

    @diffusion.command(help="diffusion_delete_help", description="diffusion_delete_description")
    @commands.check(is_super_admin)
    async def delete(self, ctx, diffusion_name: str):
        """ Deletes a diffusion channel, this commands is reserved to super admins """

        pass

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