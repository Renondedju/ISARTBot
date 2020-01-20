# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2018-2020 Renondedju

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

__title__     = 'Isartbot'
__authors__   = ('Renondedju', '6xray', 'Torayl', 'Lunatik', 'Ayven-Johan')
__license__   = 'MIT'
__version__   = '2.0.0'
__copyright__ = 'Copyright 2018-2020 Renondedju'

from collections import namedtuple

VersionInfo  = namedtuple('VersionInfo', 'major minor micro releaselevel')
version_info = VersionInfo(major=2, minor=0, micro=0, releaselevel='live')

from .bot import Bot