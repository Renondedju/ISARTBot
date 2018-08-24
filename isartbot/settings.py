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

from os.path import isfile, abspath
from json    import load, dump

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
        self.__path     = abspath(path)

        if not isfile(self.__path):
            print("/!\\ ISART-Bot : Settings file not found at {}. Aborting /!\\".
                format(self.__path))
            exit(1)

        with open(self.__path, 'r', encoding='utf-8') as f:
            self.__settings["settings"] = load(f)

    def save(self):

        if isfile(self.__path):
            with open(self.__path, 'w', encoding='utf-8') as f:
                dump(self.__settings["settings"], f, indent=4, sort_keys=True)

    def __getkey(self, dictionary: dict, key: str):
        """
        Gets a key
        """
        
        real_key = key
        
        if dictionary is None:
            return None

        if '_' + key in dictionary:
            real_key = '_' + key

        elif not key in dictionary:
            return None

        return dictionary.get(real_key)

    def __writekey(self, dictionary: dict, key: str, data):
        """
            Writes a key if this key isn't protected
            returns true if the write is successful
        """

        if dictionary is None:
            return False

        #Updating a key
        if key in dictionary:
            dictionary[key] = data
            self.save()
            return True

        #Adding a new key
        elif key not in dictionary and '_' + key not in dictionary:
            dictionary[key] = data
            self.save()
            return True

        return False

    def __delkey(self, dictionary: dict, key: str):
        """
            Deletes a key from a dict
        """

        if dictionary is None:
            return False

        dictionary.pop(      key, None)
        dictionary.pop('_' + key, None)

        self.save()

    def get(self, *args, **kwargs):
        """
        Return the requested element
        """
        data = self.__settings.get("settings")
        
        command = kwargs.get('command', '')
        if (command != None and command != ""):
            data = self.__getkey(self.__getkey(self.__getkey(data, "bot"), "commands"), command)

        for i in range(len(args)):
            data = self.__getkey(data, args[i])

        return data

    def write(self, data, key, *args, **kwargs):
        """
        Writes an element into the settings
        """

        dictionary = self.__settings.get("settings")
        
        command = kwargs.get('command', '')
        if (command != None and command != ""):
            dictionary = self.__getkey(self.__getkey(self.__getkey(dictionary, "bot"), "commands"), command)

        for i in range(len(args)):
            dictionary = self.__getkey(dictionary, args[i])

        return self.__writekey(dictionary, key, data)

    def delete(self, key, *args, **kwargs):
        """ Deletes a key from the settings """

        dictionary = self.__settings.get("settings")
        
        command = kwargs.get('command', '')
        if (command != None and command != ""):
            dictionary = self.__getkey(self.__getkey(self.__getkey(dictionary, "bot"), "commands"), command)

        for i in range(len(args)):
            dictionary = self.__getkey(dictionary, args[i])

        return self.__delkey(dictionary, key)

    @property
    def path(self):
        """
        Returns the path of the file loaded.
        """
        return self.__path