"""picture.py

PictureClerk - The little helper for your picture workflow.
This file contains the Picture class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


import sys
import os.path


class PictureFileType():
    RAW = 0
    JPG = 1


class Picture():
    """
    A Picture object stores the history, metadata, sidecar files and more for a
    picture file.
    
    Constructor arguments:
        path (string)   :   absolute path to the picture file
    """

    def __init__(self, path):
        # TODO: Maybe test if two pictures are the same file using os.path.samefile
        self.path = os.path.realpath(path)
        if not os.path.exists(path):
            print "Invalid path."
            sys.exit(1)
        # FIXME: extract file type from given filename
        self.filetype = PictureFileType.RAW
        # sidecar files
        self.sidecar = []
        # metadata
        #self.metadata = 
        # history
        self.history = []


