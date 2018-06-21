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

    @property
    def get(self):
        """
        Get property : this is the only way to access loaded setting 
        """
        return self.__settings["settings"]

    @property
    def path(self):
        """
        Returns the path of the file loaded.
        """
        return self.__path