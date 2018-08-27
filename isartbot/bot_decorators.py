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

async def is_isartian(ctx):
    """
        Checks if the author is an isartian
    """

    isartian = discord.utils.get(ctx.guild.roles, 
        id = ctx.bot.settings.get('bot', 'isartian_role_id'))

    if (isartian is None):
        ctx.bot.logs.print("Isartian role is empty !")
        return False

    result = isartian in ctx.author.roles

    if (result is False):
        await ctx.bot.send_fail(ctx, 
            "Sorry but you need to be have the isartian role to do that",
            "Check")

    return result

def is_admin(ctx):
    """ 
        Checks if the author is an admin
    """
    if ctx.bot.settings.get("debug") and is_dev(ctx):
        return True
        
    return ctx.author.guild_permissions.administrator