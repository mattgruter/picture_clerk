"""local_connector.py

PictureClerk - The little helper for your picture workflow.
This file contains the LocalConnector class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2011/04/24 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


import os


from connector import Connector
#from connector import ConnectionError


class LocalConnector(Connector):
    """
    LocalConnector objects hold the logic on how to connect to local filesystem
    paths.
    This class inherits from the Connector base class.
    """
    def __init__(self, url):
        Connector.__init__(self, url)
        
    def _connect(self):
        """
        Establish a local connection
        
        Raises ConnectionError
        """
        # TODO: should connect check if path exists?
#        if not os.path.exists(self.url.path):
#            raise ConnectionError(self.url)
        return
        
        
    def _disconnect(self):
        """
        Close local connection (do nothing ;-))
        """
        return
            
    def _open(self, filename, mode):
        """
        Open the specified file and return a file handle
        """
        return open(os.path.join(self.url.path, filename), mode)
            
    def _mkdir(self, rel_path, mode):
        """
        Create the specified directory
        """
        if rel_path == '.':
            path = self.url.path
        else:
            path = os.path.join(self.url.path, rel_path)
        os.mkdir(path, mode)
        
