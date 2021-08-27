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

from isartbot.exceptions import UnauthorizedCommand
from isartbot.checks     import developper

async def is_super_admin(ctx):
    value = super_admin(ctx, ctx.author)

    if (not value):
        raise UnauthorizedCommand(missing_status = await ctx.bot.get_translation(ctx, "super_admin_status", force_fetch = True))

    return True

# Manual check
def super_admin(ctx, user):
    return str(user.id) in ctx.bot.settings.get('common', 'super_admins') or\
         (ctx.bot.dev_mode and developper(ctx, user))