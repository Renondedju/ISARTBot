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
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN TH
# SOFTWARE.

from sqlalchemy     import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship, backref

from isartbot.database import TableBase

class DiffusionSubscription(TableBase):

    __tablename__ = 'diffusion_subscriptions'

    id                 = Column('id'         , Integer, primary_key=True, unique=True)
    tag                = Column('discord_tag', Text   , default = "")
    discord_channel_id = Column('channel_id' , Integer, nullable=False)

    diffusion_id       = Column(Integer, ForeignKey('diffusions.id'))
    server_id          = Column(Integer, ForeignKey('servers.id'   ))

    diffusion          = relationship('Diffusion', backref=backref('subscriptions' , cascade='all,delete,delete-orphan'))
    server             = relationship('Server'   , backref=backref('diffusion_subs', cascade='all,delete,delete-orphan'))