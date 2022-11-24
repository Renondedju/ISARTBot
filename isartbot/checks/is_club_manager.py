# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018-2021 Renondedju

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

from isartbot.checks        import developper
from isartbot.exceptions    import UnauthorizedCommand

async def is_club_manager(ctx):
    value = club_manager(ctx, ctx.author) or\
             ctx.author.permissions_in(ctx.channel).administrator or \
            (ctx.bot.dev_mode and developper(ctx, ctx.author))

    if (not value):
        raise UnauthorizedCommand(missing_status = await ctx.bot.get_translation(ctx, "club_manager_status", force_fetch = True))

    return True

def club_manager(ctx, user):
    target_role = ctx.guild.get_role(ctx.bot.settings.getint('reservation', 'club_manager_role_id'))

    return target_role in user.roles
