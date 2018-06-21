"""
@author : Basile Combet
@brief  : Settings class

"""

import json

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
            self.__settings["settings"] = json.load(f)

    def get(self, *args):
        """
        Return the requested element
        """
        
        data = self.__settings["settings"]
        for i in range(len(args)):
            data = data[args[i]]

        return data

    @property
    def path(self):
        """
        Returns the path of the file loaded.
        """
        return self.__path