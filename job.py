"""job.py

PictureClerk - The little helper for your picture workflow.
This file contains the Job class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2007 Matthias Grueter"
__license__ = "GPL"


# TODO: unit tests
class Job():
    """Class to organize job orders for workers

    Constructor arguments:
        bin (string)    :   binary to execute
        args (list)     :   arguments to be passed to binary
        descr (string)  :   descriptive text for use in logging and such.
    """
    
    def __init__(self, bin, args, descr):
        self.bin = bin
        self.args = args
        self.descr = descr


# Unit test       
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()


