"""
@author : Basile Combet
@brief  : Logs class file
"""

from datetime import datetime

class Logs():
    """
    Used to log any activity
    """

    def __init__(self, dir: str = "./logs.log", enabled: bool = True):

        #Public
        self.enabled = enabled

        #Private
        self.__logs_file = None

        #Setup
        try:
            self.__logs_file = open(dir, "a")
        except:
            self.__logs_file = None
            print("Warning : no logs file found !")

    def print(self, *args):
        """
        Logs every args into the console and
        the file (if the opening is successful)
        """

        #Generating the output
        str_args = []
        for i in range(len(args)):
            str_args.append(str(args[i]))

        output = " "
        output = output.join(args)
        date   = datetime.now().strftime('%Y/%m/%d at %H:%M:%S')
        output = date + " - " + output

        print(output)
        if (self.__logs_file != None and self.__logs_file.writable()):
            self.__logs_file.write(output + '\n')

        return

    def __del__(self):

        if (self.__logs_file != None):
            self.__logs_file.close()