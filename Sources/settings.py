# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2018 Renondedju

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
import re

class Settings():
    """
    Class used to load and store general settings
    Any settings can be loaded from a .json file only
    """

    def __init__(self, path: str = "./settings.json"):
        """
        Initializing the settings from a json file
        """

        self.__settings = {"settings": {}}
        self.__path     = path

        with open(path) as f:
            data = re.sub(r"//.*\n|\/\*[\s\S]*?(?:\*\/)", "", f.read())
            self.__settings["settings"] = json.loads(data)

    def get(self, *args, **kwargs):
        """
        Return the requested element
        """
        data = self.__settings["settings"]
        
        command = kwargs.get('command', None)
        if (command != None and command != ""):
            data = data["bot"]["commands"][command]

        for i in range(len(args)):
            data = data[args[i]]

        return data

    @property
    def path(self):
        """
        Returns the path of the file loaded.
        """
        return self.__path