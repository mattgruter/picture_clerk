"""job.py

PictureClerk - The little helper for your picture workflow.
This file contains the Job class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


import config
from picture import Picture


# TODO: unit tests
class Job():
    """Class to organize job orders for workers

    Constructor arguments:
        picture (Picture)   :   Picture which will be processed by this job
        seq_num (int)       :   sequence number for batch job tracking
        descr (string)      :   descriptive text for use in logging and such
    """
    
    def __init__(self, picture, seq_num, descr):
        self.picture = picture
        self.seq_num = seq_num
        self.descr = descr


class DCRawThumbJob(Job):
    def __init__(self, picture, seq_num):
        Job.__init__(self, picture, seq_num, 'Extracting thumbnails')
        self.bin = config.DCRAW_BIN
        self.args = ['-e', self.picture.filename]


# Unit test       
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

