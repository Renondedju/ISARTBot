# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018 Renondedju

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

import asyncio
import discord

def dont_run(ctx):
    """
        Just prevents the command from being runned
    """

    return False

def is_dev(ctx):
    """
        Checks if the author is one of the
        authors specified in the settings.json file
    """

    for id in ctx.bot.settings.get("bot", "developers_id"):
        if id == ctx.author.id:
            return True

    return False

async def is_author_in_role(ctx, id : int):
    role = discord.utils.get(ctx.guild.roles, id=id)

    if (role is None):
        ctx.bot.logs.print("Role with id " + str(id) + " does not exist.")
        return False

    result = role in ctx.author.roles

    if (result is False):
        await ctx.bot.send_fail(ctx,
            "Sorry but you need at least the role " + role.name + " to do that",
            "Check")

    return result

async def is_isartian(ctx):
    """
        Checks if the author is an Isartian
    """

    return await is_author_in_role(ctx, ctx.bot.settings.get('bot', 'isartian_role_id')) or await is_alumni(ctx)

async def is_alumni(ctx):
    """
        Checks if the author is an Alumni
    """
    return await is_author_in_role(ctx, ctx.bot.settings.get('bot', 'alumni_role_id'))

async def is_dragon(ctx):
    """
        Checks if the author has the E-SART Dragons role
    """
    return await is_moderator(ctx) or await is_author_in_role(ctx, ctx.bot.settings.get('bot', 'dragon_role_id'))

async def is_moderator(ctx):
    """
        Checks if the author is a Moderator
    """
    return is_admin(ctx) or await is_author_in_role(ctx, ctx.bot.settings.get('bot', 'dragon_role_id'))

def is_admin(ctx):
    """
        Checks if the author is an admin
    """

    if ctx.bot.settings.get("debug") and is_dev(ctx):
        return True

    return ctx.author.guild_permissions.administrator
