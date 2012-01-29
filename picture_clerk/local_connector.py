"""
Created on 2011/04/24

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""

import os

from connector import Connector
from connector import ConnectionError


class LocalConnector(Connector):
    
    """Holds logic on how to connect to local paths, extends Connector class."""
    
    def __init__(self, url):
        """LocalConnector's constructor.
        
        Arguments:
        url -- connector's base path URL, type urlparser.ParseResult or compat.
               can be relative (rel/path/...) or absolute (/abs/path/...)
               the path can be prefixed by the filesystem scheme: file:///...
        
        """
        Connector.__init__(self, url)
        
    def _connect(self):
        # Establish a local connection; raises ConnectionError.
        # overrides Connector._connect
        if not os.path.exists(self.url.path):
            raise ConnectionError(self.url)
        return

    def _disconnect(self):
        # Disconnect local connection (i.e. do nothing ;-)).
        # overrides Connector._disconnect
        return
            
    def _open(self, path, mode):
        # Open file at supplied path and return file handle.
        # overrides Connector._open
        return open(path, mode)
            
    def _mkdir(self, path, mode):
        # Create a directory at the supplied path.
        # overrides Connector._mkdir
        os.mkdir(path, mode)
        